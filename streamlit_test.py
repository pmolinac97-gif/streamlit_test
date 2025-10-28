import streamlit as st
import paho.mqtt.client as mqtt
import ssl
import time
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------------------------
# CONFIGURACIÓN MQTT
# -------------------------------------------------
BROKER = "9a0009749d5f43108523a1c28e1412c7.s1.eu.hivemq.cloud"#"t181df20.ala.eu-central-1.emqxsl.com"
PORT = 8883
USERNAME = "Test1234"
PASSWORD = "Test1234"

# -------------------------------------------------
# ESTADO GLOBAL
# -------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'device' not in st.session_state:
    st.session_state.device = ""
if 'app_state' not in st.session_state:
    st.session_state.app_state = "IDLE"
if 'measurements' not in st.session_state:
    st.session_state.measurements = []
if 'connection_checked' not in st.session_state:
    st.session_state.connection_checked = False
if 'device_on' not in st.session_state:
    st.session_state.device_on = False


# -------------------------------------------------
# FUNCIÓN DE LOGIN
# -------------------------------------------------
def login_screen():
    st.title("🔐 Acceso al Sistema de Medición MQTT")
    st.write("Por favor, introduce tus credenciales de acceso:")

    user = st.text_input("Usuario", placeholder="Tu nombre de usuario")
    device = st.text_input("Identificador de dispositivo", placeholder="Ej: DEVICE_001")

    if st.button("Entrar", type="primary"):
        if user.strip() and device.strip():
            st.session_state.user = user.strip()
            st.session_state.device = device.strip()
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.warning("Por favor, introduce ambos campos antes de continuar.")


# -------------------------------------------------
# FUNCIONES MQTT
# -------------------------------------------------
def test_connection():
    """Verifica la conexión con el broker MQTT"""
    try:
        client = mqtt.Client()
        client.username_pw_set(USERNAME, PASSWORD)
        client.tls_set_context(ssl.create_default_context())

        connected = False

        def on_connect(client, userdata, flags, rc):
            nonlocal connected
            if rc == 0:
                connected = True
            client.disconnect()

        client.on_connect = on_connect
        client.connect(BROKER, PORT, 5)
        client.loop_start()
        time.sleep(2)
        client.loop_stop()
        client.disconnect()
        return connected
    except Exception:
        return False


def check_device_on():
    """Comprueba si el dispositivo está encendido mediante /device_on"""
    try:
        device_on = False

        def on_message(client, userdata, msg):
            nonlocal device_on
            if msg.topic == "/device_on" and msg.payload.decode().strip() == "1":
                device_on = True

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe("/device_on")

        client = mqtt.Client()
        client.username_pw_set(USERNAME, PASSWORD)
        client.tls_set_context(ssl.create_default_context())
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(BROKER, PORT, 5)
        client.loop_start()
        time.sleep(1.5)
        client.loop_stop()
        client.disconnect()

        st.session_state.device_on = device_on
        return device_on

    except Exception:
        return False


def collect_measurements_until_ack():
    """Recoge mediciones desde /measure hasta recibir un ACK"""
    try:
        ack_received = False
        measurements = []

        def on_message(client, userdata, msg):
            nonlocal ack_received
            topic = msg.topic
            payload = msg.payload.decode().strip()

            if topic == "/ack" and payload == "1":
                ack_received = True
            elif topic == "/measure" and ',' in payload:
                try:
                    x, y = map(float, payload.split(','))
                    measurements.append((x, y))
                except ValueError:
                    pass

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe("/ack")
                client.subscribe("/measure")

        client = mqtt.Client()
        client.username_pw_set(USERNAME, PASSWORD)
        client.tls_set_context(ssl.create_default_context())
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(BROKER, PORT, 60)
        client.loop_start()

        start_time = time.time()
        while not ack_received:
            if time.time() - start_time > 300:
                break
            if st.session_state.app_state != "WAITING_ACK":
                break
            time.sleep(0.1)

        client.loop_stop()
        client.unsubscribe("/ack")
        client.unsubscribe("/measure")
        client.disconnect()

        return ack_received, measurements

    except Exception as e:
        st.error(f"Error en comunicación MQTT: {e}")
        return False, []


def publish_message(topic, message):
    """Publica un mensaje en un topic"""
    try:
        client = mqtt.Client()
        client.username_pw_set(USERNAME, PASSWORD)
        client.tls_set_context(ssl.create_default_context())

        client.connect(BROKER, PORT, 5)
        client.loop_start()
        time.sleep(0.5)
        client.publish(topic, message)
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()
        return True
    except Exception as e:
        st.error(f"Error publicando: {e}")
        return False


def plot_measurements():
    """Grafica las mediciones"""
    if not st.session_state.measurements:
        st.warning("No hay mediciones para graficar")
        return False

    try:
        x_values = [x for x, _ in st.session_state.measurements]
        y_values = [y for _, y in st.session_state.measurements]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x_values, y_values, 'b-', marker='o', linewidth=2, markersize=4)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title(f'Mediciones ({len(x_values)} puntos)')
        ax.grid(True, alpha=0.3)

        st.pyplot(fig)

        df = pd.DataFrame({'X': x_values, 'Y': y_values})
        st.write("Datos recolectados:")
        st.dataframe(df)
        return True

    except Exception as e:
        st.error(f"Error graficando: {e}")
        return False


# -------------------------------------------------
# INTERFAZ PRINCIPAL
# -------------------------------------------------
if not st.session_state.logged_in:
    login_screen()
else:
    st.title("📡 Sistema de Medición MQTT")

    # Información superior
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Usuario", st.session_state.user)
    with col2:
        st.metric("Dispositivo", st.session_state.device)
    with col3:
        connected = test_connection()
        st.metric("Broker MQTT", "Conectado" if connected else "Desconectado")

    st.write("---")

    # Estado del dispositivo
    device_on = check_device_on()
    st.metric("Estado del dispositivo", "Encendido" if device_on else "Apagado")

    # Estado de la aplicación
    state_labels = {
        "IDLE": "Esperando Start",
        "WAITING_ACK": "Midiendo",
        "PLOTTING": "Listo para nuevo ciclo"
    }
    current_state_label = state_labels.get(st.session_state.app_state, "Desconocido")
    st.info(f"**Estado actual:** {current_state_label}")

    # --- Lógica de estados ---
    if st.session_state.app_state == "IDLE":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start", type="primary"):
                if publish_message("/start", "1"):
                    st.session_state.app_state = "WAITING_ACK"
                    st.session_state.measurements = []
                    st.rerun()
        with col2:
            if st.button("Probar Conexión"):
                connected = test_connection()
                if connected:
                    st.success("✅ Conectado al broker MQTT")
                else:
                    st.error("❌ Desconectado del broker MQTT")

    elif st.session_state.app_state == "WAITING_ACK":
        st.info("⏳ Midiendo... Esperando ACK en /ack")
        ack_received, measurements = collect_measurements_until_ack()

        if ack_received:
            st.session_state.measurements = measurements
            st.session_state.app_state = "PLOTTING"
            st.success(f"✅ ACK recibido - {len(measurements)} mediciones recolectadas")
        else:
            st.session_state.app_state = "IDLE"
            st.error("❌ No se recibió ACK o se canceló la operación")

        st.rerun()

    elif st.session_state.app_state == "PLOTTING":
        st.success("✅ Mediciones completas - Gráfico y datos:")
        plot_measurements()

        if st.button("Nuevo Ciclo", type="primary"):
            st.session_state.app_state = "IDLE"
            st.session_state.measurements = []
            st.rerun()

    # -------------------------------------------------
    # SECCIÓN DE CALIBRACIÓN
    # -------------------------------------------------
    st.write("---")
    st.subheader("Calibración MQTT")

    uploaded_file = st.file_uploader("Selecciona un archivo .txt para enviar a /calibration", type=["txt"])

    if uploaded_file is not None:
        file_content = uploaded_file.read().decode("utf-8").strip()

        st.text_area("Contenido del archivo:", file_content, height=200)

        if st.button("Enviar archivo a /calibration", type="primary"):
            try:
                for line in file_content.splitlines():
                    if line.strip():
                        publish_message("/calibration", line.strip())
                        time.sleep(0.1)
                st.success("Archivo enviado correctamente al topic /calibration")
            except Exception as e:
                st.error(f"Error enviando el archivo: {e}")

    st.write("---")
    st.write("Broker:", BROKER)
    st.write("Puerto:", PORT)
