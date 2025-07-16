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
        "descripcion": "Diseñado entre 1988 y 1990 por Rogelio Salmona y su equipo, el edificio del actual Centro Cultural de Cali está ubicado en el barrio La Merced. Inicialmente construido para oficinas de la corporación financiera FES, fue adquirido por el Municipio en 1997 y hoy alberga la Secretaría de Cultura, el Archivo Histórico y el Centro Cultural. Fue galardonado con el Premio Nacional de Arquitectura en 1992, aunque no está declarado Bien de Interés Cultural. Se encuentra en el barrio La Merced, zona reconocida como sector histórico y de interés cultural desde 1959.",
        "lat": 3.453566, "lon": -76.533091
    },
    "01_teatro municipal enrique buenaventura": {
        "descripcion": "Inaugurado en 1927 y con su vestíbulo finalizado en 1940, el Teatro Municipal fue diseñado por los ingenieros Borrero y Ospina, con muros portantes de ladrillo y entrepisos de madera. Su estilo combina una fachada barroca clasicista francesa con una planta en herradura tipo 'teatro a la italiana'. A lo largo del tiempo, se han realizado intervenciones, como el cambio de nivel de la platea en 1953 y una ampliación moderna en los años 80, que integró áreas de servicio.",
        "lat": 3.451814, "lon": -76.532483
    },
    # ... (resto de las clases_info)
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

    # Mover el bloque try dentro del if uploaded_file
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

                if "lat" in info and "lon" in info:
                    mapa = folium.Map(location=[info["lat"], info["lon"]], zoom_start=16)
                    folium.Marker(
                        location=[info["lat"], info["lon"]],
                        popup=clase_detectada.title(),
                        tooltip="Ver ubicación"
                    ).add_to(mapa)

                    st.markdown("<h5 style='text-align: center;'>Ubicación en el mapa:</h5>", unsafe_allow_html=True)
                    st_folium(mapa, width=600, height=400)
            else:
                st.markdown("<p style='text-align: center; color: red;'>La clase detectada no está registrada en el diccionario.</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align: center; font-size: 24px;'>No se detectaron objetos.</p>", unsafe_allow_html=True)

    except Exception as e:
        st.markdown(f"<p style='text-align: center; font-size: 18px; color: red;'>Error: {str(e)}</p>", unsafe_allow_html=True)
