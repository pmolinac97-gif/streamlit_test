# -*- coding: utf-8 -*-
import streamlit as st
import paho.mqtt.client as mqtt
import ssl
import time
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------------------------
# CONFIGURACION MQTT
# -------------------------------------------------
BROKER = "9a0009749d5f43108523a1c28e1412c7.s1.eu.hivemq.cloud"
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
if 'battery_low' not in st.session_state:
    st.session_state.battery_low = False

# -------------------------------------------------
# VARIABLES CLINICAS GLOBALES
# -------------------------------------------------
if 'patient_id' not in st.session_state:
    st.session_state.patient_id = ""
if 'patient_height' not in st.session_state:
    st.session_state.patient_height = ""
if 'patient_weight' not in st.session_state:
    st.session_state.patient_weight = ""
if 'patient_distance' not in st.session_state:
    st.session_state.patient_distance = ""
if 'patient_gender' not in st.session_state:
    st.session_state.patient_gender = ""
if 'clinical_data_saved' not in st.session_state:
    st.session_state.clinical_data_saved = False

# -------------------------------------------------
# APLICAR ESTILOS PERSONALIZADOS
# -------------------------------------------------
def apply_custom_styles():
    st.markdown("""
    <style>
        /* --- GENERAL --- */
        html, body, [class*="css"]  {
            margin: 0 !important;
            padding: 0 !important;
            font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #ffffff !important;
            color: #333333 !important;
        }

        /* Elimina espacio superior */
        section.main > div:first-child {
            padding-top: 0rem !important;
        }

        /* Título principal */
        h1 {
            color: #f58020 !important;
            font-weight: 700 !important;
            margin-top: 0 !important;
            margin-bottom: 0.5rem !important;
        }

        h2, h3 {
            color: #f58020 !important;
            font-weight: 600 !important;
        }

        /* Texto general */
        .stMarkdown, .stText, .stLabel {
            color: #333333 !important;
            font-size: 1rem !important;
        }

        /* Campos de entrada */
        .stTextInput input, .stTextArea textarea {
            background-color: #ffffff !important;
            color: #333333 !important;
            border: 1px solid #cccccc !important;
            border-radius: 6px !important;
            padding: 10px !important;
        }

        /* Botones */
        .stButton button {
            background-color: #f58020 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            padding: 0.6rem 1.2rem !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.2s ease-in-out;
        }

        .stButton button:hover {
            background-color: #e07010 !important;
            transform: translateY(-1px);
        }

        /* Botón secundario */
        .stButton button[kind="secondary"] {
            background-color: #6c757d !important;
        }

        .stButton button[kind="secondary"]:hover {
            background-color: #5a6268 !important;
        }

        /* Métricas */
        [data-testid="stMetricValue"] {
            color: #f58020 !important;
            font-weight: 700 !important;
            font-size: 1.3rem !important;
        }

        [data-testid="stMetricLabel"] {
            color: #555555 !important;
            font-size: 0.9rem !important;
        }

        [data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #dddddd !important;
            border-radius: 10px !important;
            padding: 15px !important;
            margin: 5px !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        }

        /* Columnas más anchas */
        .block-container {
            padding-top: 0rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            max-width: 1400px !important;
        }

        /* Tablas */
        .dataframe {
            background-color: #ffffff !important;
            border: 1px solid #dddddd !important;
            color: #333333 !important;
        }

        .dataframe th {
            background-color: #f8f9fa !important;
            color: #f58020 !important;
            font-weight: bold !important;
        }

        .dataframe td {
            background-color: #ffffff !important;
            border-bottom: 1px solid #eeeeee !important;
        }

        /* Contenedores */
        .element-container {
            background-color: #ffffff !important;
            border-radius: 8px !important;
            padding: 15px !important;
            margin: 10px 0 !important;
            border: 1px solid #dddddd !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #dddddd !important;
        }

        /* Alertas */
        .stAlert {
            border-radius: 8px !important;
            border-left: 5px solid #f58020 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 18px;
            background-color: #f8f9fa !important;
            padding: 10px !important;
            border-radius: 8px !important;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: #ffffff !important;
            color: #333333 !important;
            border: 1px solid #dddddd !important;
            border-radius: 6px !important;
            padding: 8px 16px !important;
            transition: all 0.2s ease-in-out;
        }

        .stTabs [aria-selected="true"] {
            background-color: #f58020 !important;
            color: #ffffff !important;
            border-color: #e07010 !important;
        }

        /* File uploader */
        .stFileUploader {
            background-color: #ffffff !important;
            border: 2px dashed #f58020 !important;
            border-radius: 8px !important;
            padding: 20px !important;
        }

        /* Gráficos */
        canvas {
            background-color: #ffffff !important;
        }

    </style>
    """, unsafe_allow_html=True)


# Aplicar estilos
apply_custom_styles()

# -------------------------------------------------
# FUNCION DE LOGIN
# -------------------------------------------------
def login_screen():
    st.title("Acceso al sistema de medición CONIBEE")
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
    """Verifica la conexion con el broker MQTT"""
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

def check_device_status():
    """Comprueba el estado del dispositivo y la batería mediante /device_on y /low_battery"""
    try:
        device_on = False
        battery_low = False

        def on_message(client, userdata, msg):
            nonlocal device_on, battery_low
            if msg.topic == "/device_on" and msg.payload.decode().strip() == "1":
                device_on = True
            elif msg.topic == "/low_battery" and msg.payload.decode().strip() == "1":
                battery_low = True

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe("/device_on")
                client.subscribe("/low_battery")

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
        st.session_state.battery_low = battery_low
        return device_on, battery_low

    except Exception:
        return False, False

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
        st.error(f"Error en comunicacion MQTT: {e}")
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
        # Configurar estilo de matplotlib para que coincida con el tema claro
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x_values = [x for x, _ in st.session_state.measurements]
        y_values = [y for _, y in st.session_state.measurements]

        ax.plot(x_values, y_values, color='#f58020', linewidth=2, markersize=4)
        ax.set_xlabel('X', color='#333333')
        ax.set_ylabel('Y', color='#333333')
        ax.set_title(f'Mediciones ({len(x_values)} puntos)', color='#333333')
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('#ffffff')
        fig.patch.set_facecolor('#ffffff')
        
        # Color de los ejes
        ax.spines['bottom'].set_color('#333333')
        ax.spines['top'].set_color('#333333')
        ax.spines['right'].set_color('#333333')
        ax.spines['left'].set_color('#333333')
        ax.tick_params(colors='#333333')

        st.pyplot(fig)

        
        # df = pd.DataFrame({'X': x_values, 'Y': y_values})
        # st.write("Datos recolectados:")
        # st.dataframe(df)
        
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
    st.title("CONIBEE")

    # Informacion superior
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Usuario", st.session_state.user)
    with col2:
        st.metric("Dispositivo", st.session_state.device)
    with col3:
        connected = test_connection()
        st.metric("Conectividad", f" {'Conectado' if connected else 'Desconectado'}")
    with col4:
        device_on, battery_low = check_device_status()
        st.metric("Estado del dispositivo", f"{'Encendido' if device_on else 'Apagado'}")
    with col5:
        battery_status = "Baja" if battery_low else "Cargada"
        battery_color = "#ff4b4b" if battery_low else "#f58020"
        st.metric("Estado de la batería", f"{battery_status}")

    # Mostrar alerta si la batería está baja
    if battery_low:
        st.error("**Alerta:** La batería del dispositivo está baja. Por favor, cargue el dispositivo antes de realizar mediciones prolongadas.")

    #st.write("---")
    # -------------------------------------------------
    # SECCION DE CALIBRACION
    # -------------------------------------------------
    #st.write("---")
    st.subheader("Calibración del dispositivo")

    uploaded_file = st.file_uploader("Selecciona un archivo .txt para enviar a /calibration", type=["txt"])

    if uploaded_file is not None:
        file_content = uploaded_file.read().decode("utf-8").strip()

        # st.text_area("Contenido del archivo:", file_content, height=200)

        if st.button("Enviar archivo a /calibration", type="primary"):
            try:
                for line in file_content.splitlines():
                    if line.strip():
                        publish_message("/calibration", line.strip())
                        time.sleep(0.1)
                st.success("Archivo enviado correctamente al topic /calibration")
            except Exception as e:
                st.error(f"Error enviando el archivo: {e}")

    #st.write("---")
    # -------------------------------------------------
    # SECCION DE DATOS CLINICOS
    # -------------------------------------------------
    st.subheader("Información clínica")
    
    # Crear columnas para los campos de entrada
    col1, col2 = st.columns(2)
    
    with col1:
        patient_id = st.text_input(
            "ID paciente", 
            value=st.session_state.patient_id,
            placeholder="Ej: PAC001"
        )
        patient_height = st.text_input(
            "Altura (cm)", 
            value=st.session_state.patient_height,
            placeholder="Ej: 175"
        )
        patient_weight = st.text_input(
            "Peso (kg)", 
            value=st.session_state.patient_weight,
            placeholder="Ej: 70"
        )
    
    with col2:
        patient_distance = st.text_input(
            "Distancia (cm)", 
            value=st.session_state.patient_distance,
            placeholder="Ej: 100"
        )
        patient_gender = st.selectbox(
            "Género",
            options=["", "Masculino", "Femenino"],
            index=0 if not st.session_state.patient_gender else 
                  (1 if st.session_state.patient_gender == "Masculino" else 2)
        )
    
    # Botón para guardar los datos clínicos
    if st.button("Guardar datos clínicos", type="primary"):
        if patient_id.strip():
            # Guardar en variables globales del sistema
            st.session_state.patient_id = patient_id.strip()
            st.session_state.patient_height = patient_height.strip()
            st.session_state.patient_weight = patient_weight.strip()
            st.session_state.patient_distance = patient_distance.strip()
            st.session_state.patient_gender = patient_gender
            st.session_state.clinical_data_saved = True
            
            st.success("Datos clínicos guardados correctamente")
            
            # Mostrar resumen de los datos guardados
            st.write("**Resumen de datos clínicos guardados:**")
            summary_cols = st.columns(4)
            with summary_cols[0]:
                st.metric("ID Paciente", st.session_state.patient_id)
            with summary_cols[1]:
                st.metric("Altura", f"{st.session_state.patient_height} cm" if st.session_state.patient_height else "No especificado")
            with summary_cols[2]:
                st.metric("Peso", f"{st.session_state.patient_weight} kg" if st.session_state.patient_weight else "No especificado")
            with summary_cols[3]:
                st.metric("Género", st.session_state.patient_gender if st.session_state.patient_gender else "No especificado")
            
            if st.session_state.patient_distance:
                st.metric("Distancia", f"{st.session_state.patient_distance} cm")
        else:
            st.warning("El ID paciente es obligatorio")
    
    # Mostrar datos actuales si ya están guardados
    elif st.session_state.clinical_data_saved:
        st.info("**Datos clínicos actuales guardados:**")
        summary_cols = st.columns(4)
        with summary_cols[0]:
            st.metric("ID Paciente", st.session_state.patient_id)
        with summary_cols[1]:
            st.metric("Altura", f"{st.session_state.patient_height} cm" if st.session_state.patient_height else "No especificado")
        with summary_cols[2]:
            st.metric("Peso", f"{st.session_state.patient_weight} kg" if st.session_state.patient_weight else "No especificado")
        with summary_cols[3]:
            st.metric("Género", st.session_state.patient_gender if st.session_state.patient_gender else "No especificado")
        
        if st.session_state.patient_distance:
            st.metric("Distancia", f"{st.session_state.patient_distance} cm")

    # -------------------------------------------------
    # ESTADO DEL DISPOSITIVO
    # -------------------------------------------------

    # Estado de la aplicacion
    state_labels = {
        "IDLE": "Esperando nueva medicion",
        "WAITING_ACK": "Midiendo",
        "PLOTTING": "Listo para nueva medicion"
    }
    current_state_label = state_labels.get(st.session_state.app_state, "Desconocido")
    st.info(f"**Estado actual:** {current_state_label}")

    # --- Logica de estados ---
    
    if st.session_state.app_state == "IDLE":
        # st.markdown(
            # """
            # <div style="display: flex; justify-content: center; align-items: center; margin-top: 1.5rem; margin-bottom: 1rem;">
                # <style>
                    # div[data-testid="stButton"] button {
                        # font-size: 1.1rem !important;
                        # padding: 0.8rem 2rem !important;
                        # border-radius: 8px !important;
                    # }
                # </style>
            # </div>
            # """,
            # unsafe_allow_html=True
        # )

        # Botón centrado
        col_center = st.columns([1, 1, 1])[1]
        with col_center:
            if st.button("Iniciar Medicion", type="primary"):
                if publish_message("/start", "1"):
                    st.session_state.app_state = "WAITING_ACK"
                    st.session_state.measurements = []
                    st.rerun()
                
    elif st.session_state.app_state == "WAITING_ACK":
        st.info("Midiendo...")
        ack_received, measurements = collect_measurements_until_ack()

        if ack_received:
            st.session_state.measurements = measurements
            st.session_state.app_state = "PLOTTING"
            st.success("Medicion completada")
        else:
            st.session_state.app_state = "IDLE"
            st.error("No se pudo finalizar la medicion")

        st.rerun()

    elif st.session_state.app_state == "PLOTTING":
        st.success("Mediciones completadas - Grafico y datos:")
        plot_measurements()

        if st.button("Nuevo Ciclo", type="primary"):
            st.session_state.app_state = "IDLE"
            st.session_state.measurements = []
            st.rerun()
    
    # Boton para cerrar sesion
    if st.button("Cerrar Sesion", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.session_state.device = ""
        st.session_state.app_state = "IDLE"
        st.session_state.measurements = []
        st.session_state.battery_low = False
        st.rerun()
