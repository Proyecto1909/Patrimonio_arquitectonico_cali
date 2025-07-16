import streamlit as st
import cv2
import numpy as np
import requests
import base64
from PIL import Image
from io import BytesIO
from roboflow import Roboflow
import folium
from streamlit_folium import st_folium

# Inicializar modelo Roboflow
rf = Roboflow(api_key="mdOMpQUnKHtUy9qBbQh2")
project = rf.workspace("edificios-patrimoniales").project("edificios-patrimoniales")
version = project.version(1)
model = version.model

# Configurar página
st.set_page_config(page_title="PATRIMONIO ARQUITECTÓNICO", layout="wide")

# Fondo visual desde Google Drive
def cargar_fondo(file_id):
    url = f"https://drive.google.com/uc?export=view&id={file_id}"
    response = requests.get(url)
    img_base64 = base64.b64encode(response.content).decode()
    html = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(html, unsafe_allow_html=True)

cargar_fondo("18yMlwFnVEbx7vF-H7MG5ZTzIr9SnuA2L")

# Encabezados
st.markdown("<h1 style='text-align: center; font-weight: bold;'>PATRIMONIO ARQUITECTÓNICO</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; font-weight: bold;'>Fotografía Arquitectónica de Cali</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; font-weight: bold;'>Reconoce y aprende de los edificios patrimoniales de nuestra historia.</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-weight: bold;'>Sube una imagen para analizarla</p>", unsafe_allow_html=True)

# Funciones
def image_to_base64(image_array):
    im_pil = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
    buffered = BytesIO()
    im_pil.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# Diccionario de clases con coordenadas
clases_info = {
    "00_centro cultural de cali": {
        "descripcion": "Diseñado entre 1988 y 1990 por Rogelio Salmona...",
        "lat": 3.453566, "lon": -76.533091
    },
    "01_teatro municipal enrique buenaventura": {
        "descripcion": "Inaugurado en 1927 con vestíbulo finalizado en 1940...",
        "lat": 3.451814, "lon": -76.532483
    },
    "02_teatro jorge isaacs": {
        "descripcion": "El Teatro Jorge Isaacs, de estilo italiano con ornamentación...",
        "lat": 3.451069, "lon": -76.531856
    },
    "03_iglesia de la ermita": {
        "descripcion": "Reconstruida entre 1925 y 1945 tras un terremoto...",
        "lat": 3.452551, "lon": -76.531432
    },
    "04_iglesia y convento de la merced": {
        "descripcion": "Construida entre 1541 y 1544 como parte del convento...",
        "lat": 3.453098, "lon": -76.533524
    },
    "05_edificio coltabaco": {
        "descripcion": "Edificio republicano con decoración neocolonial...",
        "lat": 3.452272, "lon": -76.532405
    },
    "06_casa proartes": {
        "descripcion": "Construida en 1871, ha sido cárcel, biblioteca y ahora centro cultural...",
        "lat": 3.451547, "lon": -76.532637
    },
    "07_edificio banco cafetero": {
        "descripcion": "Ejemplo moderno construido entre 1960 y 1962...",
        "lat": 3.452385, "lon": -76.531988
    }
}

# Subida de imagen
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    uploaded_file = st.file_uploader("Selecciona una imagen", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    img_np = np.array(image)
    cv2_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    original_height, original_width = cv2_img.shape[:2]
    new_width = 500
    ratio = new_width / original_width
    new_height = int(original_height * ratio)
    resized_img = cv2.resize(cv2_img, (new_width, new_height), interpolation=cv2.INTER_AREA)

    img_str = image_to_base64(resized_img)
    st.markdown(
        f"""
        <div style='text-align: center;'>
            <img src='data:image/jpeg;base64,{img_str}' width='500'/>
        </div>
        """, unsafe_allow_html=True
    )

    temp_filename = "temp_image.jpg"
    cv2.imwrite(temp_filename, resized_img)

    try:
        resultado = model.predict(temp_filename).json()
        if resultado['predictions']:
            clase_detectada = resultado['predictions'][0]['predictions'][0]['class'].strip().lower()

            st.markdown(
                f"<p style='text-align: center; font-size: 28px; font-weight: bold;'>Edificio: {clase_detectada.title()}</p>",
                unsafe_allow_html=True
            )

            if clase_detectada in clases_info:
                info = clases_info[clase_detectada]

                st.markdown(
                    f"""
                    <div style='
                        background-color: rgba(255,255,255,0.85);
                        border: 2px solid #555;
                        border-radius: 12px;
                        padding: 20px;
                        margin-top: 20px;
                        width: 50%;
                        margin-left: auto;
                        margin-right: auto;
                        box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
                    '>
                        <h4 style='text-align: center; color: #333; font-weight: bold;'>Reseña Histórica</h4>
                        <p style='font-size: 18px; text-align: justify; color: #222;'>{info['descripcion']}</p>
                    </div>
                    """, unsafe_allow_html=True
                )

                # Mostrar mapa
                if "lat" in info and "lon" in info:
                    mapa = folium.Map(location=[info["lat"], info["lon"]], zoom_start=16)
                    folium.Marker(
                        location=[info["lat"], info["lon"]],
                        popup=clase_detectada.title(),
                        tooltip="Ver ubicación"
                    ).add_to(mapa)

                    st.markdown("<h5 style='text-align: center;'>Ubicación en el mapa:</h5>", unsafe_allow_html=True)
                    st_folium(mapa, width=700)
            else:
                st.markdown("<p style='text-align: center; color: red;'>La clase detectada no está registrada en el diccionario.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align: center; font-size: 24px;'>No se detectaron objetos.</p>", unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"<p style='text-align: center; font-size: 18px; color: red;'>Error: {str(e)}</p>", unsafe_allow_html=True)
