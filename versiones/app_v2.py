import os
import asyncio
import uuid
import glob
import streamlit as st
import edge_tts
from deep_translator import GoogleTranslator
import speech_recognition as sr

# Configuración de la página
st.set_page_config(page_title="Traductor Avanzado", page_icon="🗣️", layout="centered")

STATIC_DIR = 'static'
os.makedirs(STATIC_DIR, exist_ok=True)

VOICE_MAPPING = {
    'en': {'name': 'Inglés', 'male': 'en-US-BrianNeural', 'female': 'en-US-EmmaNeural'},
    'es': {'name': 'Español', 'male': 'es-AR-TomasNeural', 'female': 'es-MX-DaliaNeural'},
    'fr': {'name': 'Francés', 'male': 'fr-FR-RemyNeural', 'female': 'fr-FR-DeniseNeural'},
    'de': {'name': 'Alemán', 'male': 'de-DE-ConradNeural', 'female': 'de-DE-AmalaNeural'},
    'pt': {'name': 'Portugués', 'male': 'pt-BR-AntonioNeural', 'female': 'pt-BR-FranciscaNeural'},
    'it': {'name': 'Italiano', 'it-IT-DiegoNeural': 'male', 'female': 'it-IT-ElsaNeural'}
}

# --- INICIALIZACIÓN DEL ESTADO DE SESIÓN (Memoria de la App) ---
if 'source_lang' not in st.session_state:
    st.session_state.source_lang = 'auto'
if 'target_lang' not in st.session_state:
    st.session_state.target_lang = 'en'
if 'text_input' not in st.session_state:
    st.session_state.text_input = ''

async def generate_audio(text, voice_id, output_file):
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(output_file)

def cleanup_old_audios():
    try:
        files = glob.glob(os.path.join(STATIC_DIR, "traduccion_*.mp3"))
        for f in files:
            os.remove(f)
    except Exception as e:
        print(f"Error al limpiar audios: {e}")

# --- FUNCIÓN PARA PASAR DE AUDIO A TEXTO ---
def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    # Guardar temporalmente los bytes del mic en un archivo wav
    temp_wav = os.path.join(STATIC_DIR, "temp_input.wav")
    with open(temp_wav, "wb") as f:
        f.write(audio_bytes.getbuffer())
        
    try:
        with sr.AudioFile(temp_wav) as source:
            audio_data = r.record(source)
            # Detecta usando el idioma de origen si no es 'auto', de lo contrario usa español por defecto
            lang_code = st.session_state.source_lang if st.session_state.source_lang != 'auto' else 'es'
            text = r.recognize_google(audio_data, language=lang_code)
            return text
    except sr.UnknownValueError:
        return "⚠️ No se pudo entender el audio claramente."
    except sr.RequestError:
        return "⚠️ Error de conexión con el servicio de transcripción."
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

# --- INTERFAZ ---
st.title("🗣️ Traductor Inteligente")

# Bloque de Micrófono (Audio a Texto)
st.subheader("🎙️ Dictar por Voz")
audio_file = st.audio_input("Graba tu voz para rellenar el campo de texto:")

if audio_file:
    with st.spinner("Transcribiendo audio..."):
        transcription = transcribe_audio(audio_file)
        if not transcription.startswith("⚠️"):
            st.session_state.text_input = transcription # Asigna la transcripción al campo de texto
            st.success("¡Voz transcrita con éxito!")
        else:
            st.error(transcription)

# Configuración de los idiomas (Selectores y Botón de intercambio)
st.subheader("🌐 Configuración de Idiomas")
col_src, col_btn, col_tgt = st.columns([4, 1, 4])

src_options = {'auto': 'Detectar idioma', **{k: v['name'] for k, v in VOICE_MAPPING.items()}}

with col_src:
    source_lang = st.selectbox(
        "De:", 
        options=list(src_options.keys()), 
        format_func=lambda x: src_options[x],
        key="source_lang_widget",
        index=list(src_options.keys()).index(st.session_state.source_lang)
    )
    st.session_state.source_lang = source_lang

with col_btn:
    st.write(" ") # Espacio estético
    # Botón para intercambiar
    if st.button("🔄", help="Intercambiar idiomas"):
        # Solo se puede intercambiar si el origen no es 'auto'
        if st.session_state.source_lang != 'auto':
            old_src = st.session_state.source_lang
            st.session_state.source_lang = st.session_state.target_lang
            st.session_state.target_lang = old_src
            st.rerun() # Fuerza a redibujar la pantalla con los nuevos valores
        else:
            st.warning("No puedes intercambiar si está en 'Detectar idioma'")

with col_tgt:
    target_lang = st.selectbox(
        "A:", 
        options=list(VOICE_MAPPING.keys()), 
        format_func=lambda x: VOICE_MAPPING[x]['name'],
        key="target_lang_widget",
        index=list(VOICE_MAPPING.keys()).index(st.session_state.target_lang)
    )
    st.session_state.target_lang = target_lang

# Selector de Género de Voz
voice_gender = st.selectbox("Voz de salida:", options=['female', 'male'], format_func=lambda x: 'Femenina' if x == 'female' else 'Masculina')

# Cuadro de entrada principal vinculada a la memoria de la sesión
user_query = st.text_area(
    "Texto a traducir:", 
    value=st.session_state.text_input, 
    placeholder="Escribe aquí o graba tu voz arriba...",
    key="text_area_main"
).strip()
st.session_state.text_input = user_query # Actualiza el estado si el usuario escribe a mano

# Botón de Procesar
if st.button("Traducir y Escuchar", type="primary"):
    if not user_query:
        st.error("Por favor, ingresa un texto o graba un audio primero.")
    else:
        with st.spinner("Procesando traducción..."):
            try:
                cleanup_old_audios()
                
                # Traducir
                translated_text = GoogleTranslator(source=st.session_state.source_lang, target=st.session_state.target_lang).translate(user_query)
                
                # Voz
                selected_voice = VOICE_MAPPING[st.session_state.target_lang][voice_gender]
                unique_id = uuid.uuid4().hex[:6]
                audio_filename = f"traduccion_{unique_id}.mp3"
                audio_path = os.path.join(STATIC_DIR, audio_filename)
                
                asyncio.run(generate_audio(translated_text, selected_voice, audio_path))
                
                # Mostrar resultados
                st.success("¡Hecho!")
                st.subheader("Texto Traducido:")
                st.write(translated_text)
                
                st.subheader("Audio:")
                st.audio(audio_path, format="audio/mp3")
                
            except Exception as e:
                st.error(f"Error en el proceso: {str(e)}")
