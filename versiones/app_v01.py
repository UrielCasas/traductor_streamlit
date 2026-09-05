import os
import asyncio
import uuid
import glob
import streamlit as st
import edge_tts
from deep_translator import GoogleTranslator

# Configuración de la página de Streamlit
st.set_page_config(page_title="Traductor y TTS", page_icon="🗣️", layout="centered")

STATIC_DIR = 'static'
os.makedirs(STATIC_DIR, exist_ok=True)

# Diccionario de idiomas soportados y sus voces asociadas
VOICE_MAPPING = {
    'en': {'name': 'Inglés', 'male': 'en-US-BrianNeural', 'female': 'en-US-EmmaNeural'},
    'es': {'name': 'Español', 'male': 'es-AR-TomasNeural', 'female': 'es-MX-DaliaNeural'},
    'fr': {'name': 'Francés', 'male': 'fr-FR-RemyNeural', 'female': 'fr-FR-DeniseNeural'},
    'de': {'name': 'Alemán', 'male': 'de-DE-ConradNeural', 'female': 'de-DE-AmalaNeural'},
    'pt': {'name': 'Portugués', 'male': 'pt-BR-AntonioNeural', 'female': 'pt-BR-FranciscaNeural'},
    'it': {'name': 'Italiano', 'male': 'it-IT-DiegoNeural', 'female': 'it-IT-ElsaNeural'}
}

async def generate_audio(text, voice_id, output_file):
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(output_file)

def cleanup_old_audios():
    """Borra los archivos .mp3 viejos de la carpeta static para ahorrar espacio"""
    try:
        files = glob.glob(os.path.join(STATIC_DIR, "traduccion_*.mp3"))
        for f in files:
            os.remove(f)
    except Exception as e:
        print(f"Error al limpiar audios viejos: {e}")

# --- INTERFAZ DE USUARIO EN STREAMLIT ---
st.title("🗣️ Traductor con Voz (TTS)")
st.write("Escribe un texto, selecciona los idiomas y genera la traducción con audio.")

# 1. Entradas del usuario
user_query = st.text_area("Texto a traducir:", placeholder="Escribe algo aquí...").strip()

# Crear columnas para los selectores de idioma y género
col1, col2, col3 = st.columns(3)

with col1:
    # Opciones de idioma origen (Auto + lista)
    src_options = {'auto': 'Detectar idioma', **{k: v['name'] for k, v in VOICE_MAPPING.items()}}
    source_lang = st.selectbox("De:", options=list(src_options.keys()), format_func=lambda x: src_options[x])

with col2:
    # Opciones de idioma destino
    target_lang = st.selectbox("A:", options=list(VOICE_MAPPING.keys()), format_func=lambda x: VOICE_MAPPING[x]['name'])

with col3:
    # Opción de género de voz
    voice_gender = st.selectbox("Voz:", options=['female', 'male'], format_func=lambda x: 'Femenina' if x == 'female' else 'Masculina')

# 2. Botón de acción
if st.button("Traducir y Generar Audio", type="primary"):
    if not user_query:
        st.error("El texto está vacío.")
    else:
        with st.spinner("Procesando..."):
            try:
                # Ejecutar limpieza de audios anteriores
                cleanup_old_audios()

                # Traducir
                translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(user_query)
                
                # Seleccionar la voz
                selected_voice = VOICE_MAPPING[target_lang][voice_gender]
                
                # Generar nombre único
                unique_id = uuid.uuid4().hex[:6]
                audio_filename = f"traduccion_{unique_id}.mp3"
                audio_path = os.path.join(STATIC_DIR, audio_filename)
                
                # Generar el archivo de audio de forma asíncrona
                asyncio.run(generate_audio(translated_text, selected_voice, audio_path))
                
                # --- Mostrar Resultados en Pantalla ---
                st.success("¡Traducción completada!")
                
                st.subheader("Texto Traducido:")
                st.write(translated_text)
                
                st.subheader("Audio:")
                # Streamlit reproduce el archivo de audio directamente pasándole la ruta del archivo
                st.audio(audio_path, format="audio/mp3")
                
            except Exception as e:
                st.error(f"Error en el proceso: {str(e)}")
