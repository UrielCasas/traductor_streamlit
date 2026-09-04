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
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = None
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None
if 'audio_filename' not in st.session_state:
    st.session_state.audio_filename = None

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

with st.form("translation_form"):
    
    # Selectores de idiomas en columnas con proporciones corregidas [4, 2, 4]
    col_src, col_btn, col_tgt = st.columns([4, 2, 4])
    src_options = {'auto': 'Detectar idioma', **{k: v['name'] for k, v in VOICE_MAPPING.items()}}

    with col_src:
        source_lang = st.selectbox(
            "De:", 
            options=list(src_options.keys()), 
            format_func=lambda x: src_options[x],
            index=list(src_options.keys()).index(st.session_state.source_lang)
        )

    with col_btn:
        st.write(" ") # Espacio vertical
        interchange = st.form_submit_button("🔄", help="Intercambiar idiomas")

    with col_tgt:
        target_lang = st.selectbox(
            "A:", 
            options=list(VOICE_MAPPING.keys()), 
            format_func=lambda x: VOICE_MAPPING[x]['name'],
            index=list(VOICE_MAPPING.keys()).index(st.session_state.target_lang)
        )

    voice_gender = st.selectbox("Voz de salida:", options=['female', 'male'], format_func=lambda x: 'Femenina' if x == 'female' else 'Masculina')

    st.markdown("### Texto a traducir:")
    
    # Campo de voz ubicado en el medio de la etiqueta y el cuadro de texto
    audio_file = st.audio_input("Dictar por voz (opcional):")
    
    if audio_file:
        with st.spinner("Transcribiendo..."):
            transcription = transcribe_audio(audio_file)
            if not transcription.startswith("⚠️"):
                st.session_state.text_input = transcription
            else:
                st.error(transcription)

    # Campo de texto definitivo
    user_query = st.text_area(
        label="Escribe o edita el texto aquí abajo:",
        value=st.session_state.text_input, 
        placeholder="Tu texto aparecerá aquí si dictás, o podés escribir directamente..."
    ).strip()

    # Botón principal para ejecutar traducción
    submit_button = st.form_submit_button("Traducir y Escuchar", type="primary")

# --- LÓGICA DE LOS BOTONES DEL FORMULARIO ---

if interchange:
    if source_lang != 'auto':
        st.session_state.source_lang = target_lang
        st.session_state.target_lang = source_lang
        st.session_state.text_input = user_query
        st.rerun()
    else:
        st.warning("No puedes intercambiar el idioma si está seleccionado 'Detectar idioma'.")

if submit_button:
    st.session_state.source_lang = source_lang
    st.session_state.target_lang = target_lang
    st.session_state.text_input = user_query

    if not user_query:
        st.error("Por favor, ingresa texto o graba un audio primero.")
    else:
        with st.spinner("Traduciendo y generando audio..."):
            try:
                cleanup_old_audios()
                
                # 1. Traducir y persistir en el estado
                st.session_state.translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(user_query)
                
                # 2. Generar Audio y persistir rutas
                selected_voice = VOICE_MAPPING[target_lang][voice_gender]
                unique_id = uuid.uuid4().hex[:6]
                st.session_state.audio_filename = f"traduccion_{unique_id}.mp3"
                st.session_state.audio_path = os.path.join(STATIC_DIR, st.session_state.audio_filename)
                
                asyncio.run(generate_audio(st.session_state.translated_text, selected_voice, st.session_state.audio_path))
                
            except Exception as e:
                st.error(f"Error en el proceso: {str(e)}")

# --- BLOQUE DE RESULTADOS (FUERA DEL FORMULARIO PARA EVITAR RESETEOS) ---
if st.session_state.translated_text and st.session_state.audio_path:
    st.write("---") 
    st.success("¡Traducción completada!")
    
    st.subheader("Texto Traducido:")
    st.info(st.session_state.translated_text)
    
    # Botón de copiar al portapapeles mediante JS
    js_button = f"""
    <script>
    function copyText() {{
        navigator.clipboard.writeText(`{st.session_state.translated_text}`);
        alert("¡Texto copiado al portapapeles!");
    }}
    </script>
    <button onclick="copyText()" style="
        background-color: #FF4B4B; 
        color: white; 
        border: none; 
        padding: 8px 16px; 
        border-radius: 4px; 
        cursor: pointer;
        font-weight: 500;">
        📋 Copiar Texto Traducido
    </button>
    """
    st.components.v1.html(js_button, height=45)

    st.subheader("Audio de Salida:")
    st.audio(st.session_state.audio_path, format="audio/mp3")
    
    # Botón de descarga de Streamlit nativo leyendo de la sesión persistente
    with open(st.session_state.audio_path, "rb") as file:
        st.download_button(
            label="📥 Descargar Audio MP3",
            data=file,
            file_name=st.session_state.audio_filename,
            mime="audio/mp3"
        )
