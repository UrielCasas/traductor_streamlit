import os
import asyncio
import uuid
import glob
import streamlit as st
import edge_tts
from deep_translator import GoogleTranslator
import speech_recognition as sr

# Configuración de la página
st.set_page_config(page_title="Traductor Inteligente", page_icon="🗣️", layout="centered")

STATIC_DIR = 'static'
os.makedirs(STATIC_DIR, exist_ok=True)

VOICE_MAPPING = {
    'en': {'name': 'Inglés', 'male': 'en-US-BrianNeural', 'female': 'en-US-EmmaNeural'},
    'es': {'name': 'Español', 'male': 'es-AR-TomasNeural', 'female': 'es-MX-DaliaNeural'},
    'fr': {'name': 'Francés', 'male': 'fr-FR-RemyNeural', 'female': 'fr-FR-DeniseNeural'},
    'de': {'name': 'Alemán', 'male': 'de-DE-ConradNeural', 'female': 'de-DE-AmalaNeural'},
    'pt': {'name': 'Portugués', 'male': 'pt-BR-AntonioNeural', 'female': 'pt-BR-FranciscaNeural'},
    'it': {'name': 'Italiano', 'male': 'it-IT-DiegoNeural', 'female': 'it-IT-ElsaNeural'}
}

# --- INICIALIZACIÓN DEL ESTADO DE SESIÓN ---
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

def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    temp_wav = os.path.join(STATIC_DIR, "temp_input.wav")
    with open(temp_wav, "wb") as f:
        f.write(audio_bytes.getbuffer())
        
    try:
        with sr.AudioFile(temp_wav) as source:
            audio_data = r.record(source)
            lang_code = st.session_state.source_lang if st.session_state.source_lang != 'auto' else 'es'
            text = r.recognize_google(audio_data, language=lang_code)
            return text
    except sr.UnknownValueError:
        return "⚠️ No se pudo entender el audio claramente."
    except sr.RequestError:
        return "⚠️ Error de conexión con el servicio de voz."
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

# --- INTERFAZ GRÁFICA ---
st.title("🗣️ Traductor de Texto y Voz")

# Opción A: Entrada por Micrófono (Dictar)
st.subheader("🎙️ Opción 1: Hablar para rellenar el texto")
audio_file = st.audio_input("Graba tu mensaje aquí:")

if audio_file:
    with st.spinner("Transcribiendo lo que dijiste..."):
        transcription = transcribe_audio(audio_file)
        if not transcription.startswith("⚠️"):
            st.session_state.text_input = transcription  # Llena el campo de la memoria
            st.success("¡Audio convertido a texto con éxito!")
        else:
            st.error(transcription)

# Opción B: Formulario principal (Configuración, Escritura manual y Procesamiento)
st.subheader("📝 Opción 2: Escribir o editar el texto")

with st.form("translation_form"):
    
    # Selectores de idiomas distribuidos en columnas
    col_src, col_btn, col_tgt = st.columns([4, 1, 4])
    src_options = {'auto': 'Detectar idioma', **{k: v['name'] for k, v in VOICE_MAPPING.items()}}

    with col_src:
        source_lang = st.selectbox(
            "De:", 
            options=list(src_options.keys()), 
            format_func=lambda x: src_options[x],
            index=list(src_options.keys()).index(st.session_state.source_lang)
        )

    with col_btn:
        st.write(" ") # Espacio vertical estético
        interchange = st.form_submit_button("🔄", help="Intercambiar idiomas de origen y destino")

    with col_tgt:
        target_lang = st.selectbox(
            "A:", 
            options=list(VOICE_MAPPING.keys()), 
            format_func=lambda x: VOICE_MAPPING[x]['name'],
            index=list(VOICE_MAPPING.keys()).index(st.session_state.target_lang)
        )

    # Configuración extra dentro del formulario
    voice_gender = st.selectbox("Voz de salida:", options=['female', 'male'], format_func=lambda x: 'Femenina' if x == 'female' else 'Masculina')

    # Campo de texto interactivo
    # Si usaste el micrófono, aparecerá aquí automáticamente. Si no, puedes escribir desde cero.
    user_query = st.text_area(
        "Texto a traducir:", 
        value=st.session_state.text_input, 
        placeholder="Escribe algo aquí o revisa el texto dictado arriba..."
    ).strip()

    # Botón principal del formulario
    submit_button = st.form_submit_button("Traducir y Escuchar", type="primary")

# --- LÓGICA DE PROCESAMIENTO TRAS LOS BOTONES DEL FORMULARIO ---

# Lógica del botón de intercambio de idiomas (🔄)
if interchange:
    if source_lang != 'auto':
        st.session_state.source_lang = target_lang
        st.session_state.target_lang = source_lang
        st.session_state.text_input = user_query # Conserva lo que haya escrito el usuario
        st.rerun()
    else:
        st.warning("No puedes intercambiar el idioma si está seleccionado 'Detectar idioma'.")

# Lógica del botón de traducción principal
if submit_button:
    # Guardamos los idiomas elegidos en el estado para recordar la selección
    st.session_state.source_lang = source_lang
    st.session_state.target_lang = target_lang
    st.session_state.text_input = user_query

    if not user_query:
        st.error("Por favor, ingresa texto o graba un audio primero.")
    else:
        with st.spinner("Traduciendo y generando audio de salida..."):
            try:
                cleanup_old_audios()
                
                # Traducir
                translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(user_query)
                
                # Configurar y generar la voz con Edge TTS
                selected_voice = VOICE_MAPPING[target_lang][voice_gender]
                unique_id = uuid.uuid4().hex[:6]
                audio_filename = f"traduccion_{unique_id}.mp3"
                audio_path = os.path.join(STATIC_DIR, audio_filename)
                
                asyncio.run(generate_audio(translated_text, selected_voice, audio_path))
                
                # Mostrar resultados finales en pantalla
                st.success("¡Traducción completada con éxito!")
                st.subheader("Texto Traducido:")
                st.info(translated_text)
                
                st.subheader("Audio de Salida:")
                st.audio(audio_path, format="audio/mp3")
                
            except Exception as e:
                st.error(f"Error en el proceso: {str(e)}")
