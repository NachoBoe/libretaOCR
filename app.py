import streamlit as st
import unicodedata
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from dotenv import load_dotenv
import os

# VARIABLES DE ENTORNO
dotenv_path = "./.env"
load_dotenv(dotenv_path=dotenv_path)

# Credenciales
endpoint = os.getenv("AZURE_DOC_INT_ENDPOINT")
key = os.getenv("AZURE_DOC_INT_KEY")


# Modelo en Azure
model_id = os.getenv("MODELO")

# Cliente
document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

# Función para extraer entidades
def extract_entities(image_binary):
    poller = document_analysis_client.begin_analyze_document(
        model_id=model_id, document=image_binary
    )
    result = poller.result()
    return {k: v.value for k, v in result.documents[0].fields.items()}

# Función para normalizar cadenas (eliminar espacios, mayúsculas y tildes)
def normalize_string(s):
    s = s.strip().lower()
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    s = s.replace(' ', '')
    return s

# Función para comparar cadenas normalizadas
def compare_strings(s1, s2):
    if not s1 or not s2:
        return False
    return normalize_string(s1) == normalize_string(s2)

def main():
    st.set_page_config(layout="wide")  # Ocupa todo el ancho de la pantalla

    # Título y toggle "Debug"
    title_col, debug_col = st.columns([8, 1])
    with title_col:
        st.title("Aplicación de Extracción y Comparación de Campos desde Imágenes")
    with debug_col:
        debug_mode = st.checkbox("Debug")

    # Definir los campos
    fields = ["PADRON", "MARCA", "MODELO", "AÑO", "MOTOR", "CHASIS", "MATRICULA", "TITULAR"]

    # Inicializar el estado de sesión para 'entities'
    if 'entities' not in st.session_state:
        st.session_state.entities = {}

    # Crear las columnas según el estado de 'debug_mode'
    if debug_mode:
        col1, col2, col3 = st.columns([2, 1, 1])  # Subir Imagen, Escribir Campos, Campos Extraídos
    else:
        col1, col2 = st.columns([2, 1])  # Subir Imagen, Escribir Campos

    with col1:
        # Título y botón "Validar Campos" en la misma línea
        header_col, button_col = st.columns([3, 1])
        with header_col:
            st.header("Subir Imagen")
        with button_col:
            # Botón deshabilitado si no hay imagen subida
            validate_button = st.button("Validar Campos", disabled=not st.session_state.get('uploaded_file'))

        uploaded_file = st.file_uploader(
            "Arrastra una imagen aquí o haz clic para subir", type=["png", "jpg", "jpeg"]
        )

        if uploaded_file is not None:
            # Guardar la imagen subida en el estado de sesión
            st.session_state.uploaded_file = uploaded_file
            # Mostrar la imagen subida
            st.image(uploaded_file, caption='Imagen subida', use_column_width=True)
            # Leer el binario de la imagen
            image_binary = uploaded_file.read()

            if validate_button:
                # Extraer las entidades y almacenarlas en el estado de sesión
                entities = extract_entities(image_binary)
                st.session_state.entities = entities
        else:
            st.session_state.uploaded_file = None
            st.session_state.entities = {}

    with col2:
        st.header("Escribir Campos")
        user_inputs = {}
        for field in fields:
            # Crear dos columnas para el campo y el indicador
            field_col1, field_col2 = st.columns([4, 1])
            with field_col1:
                user_input = st.text_input(field, key=f"user_{field}")
                user_inputs[field] = user_input
            with field_col2:
                # Mostrar el indicador después de la comparación
                if st.session_state.entities:
                    extracted_value = st.session_state.entities.get(field, "")
                    if compare_strings(user_input, extracted_value):
                        # Mostrar un check verde
                        st.markdown(
                            '<span style="color:green; font-size: 24px;">&#10004;</span>',
                            unsafe_allow_html=True
                        )
                    else:
                        # Mostrar una cruz roja
                        st.markdown(
                            '<span style="color:red; font-size: 24px;">&#10006;</span>',
                            unsafe_allow_html=True
                        )
                else:
                    st.write("")  # Espacio en blanco

    if debug_mode:
        with col3:
            st.header("Campos Extraídos")
            for field in fields:
                value = st.session_state.entities.get(field, "") if st.session_state.entities else ""
                # Mostrar el campo extraído (no editable)
                st.text_input(field, value=value, disabled=True, key=f"extracted_{field}")

if __name__ == "__main__":
    main()
