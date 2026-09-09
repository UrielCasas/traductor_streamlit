import os
import asyncio
import uuid
import glob
import streamlit as st
import edge_tts
from deep_translator import GoogleTranslator, MyMemoryTranslator
import speech_recognition as sr
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Configuración de la página
st.set_page_config(page_title="Traductor Inteligente", page_icon="🗣️", layout="centered")

STATIC_DIR = 'static'
os.makedirs(STATIC_DIR, exist_ok=True)

VOICE_MAPPING = {
    'en': {'name': 'Inglés', 'male': 'en-US-BrianNeural', 'female': 'en-US-EmmaNeural', 'mymemory_code': 'en-US'},
    'es': {'name': 'Español', 'male': 'es-AR-TomasNeural', 'female': 'es-MX-DaliaNeural', 'mymemory_code': 'es-AR'},
    'fr': {'name': 'Francés', 'male': 'fr-FR-RemyNeural', 'female': 'fr-FR-DeniseNeural', 'mymemory_code': 'fr-FR'},
    'de': {'name': 'Alemán', 'male': 'de-DE-ConradNeural', 'female': 'de-DE-AmalaNeural', 'mymemory_code': 'de-DE'},
    'pt': {'name': 'Portugués', 'male': 'pt-BR-AntonioNeural', 'female': 'pt-BR-FranciscaNeural', 'mymemory_code': 'pt-PT'},
    'it': {'name': 'Italiano', 'male': 'it-IT-DiegoNeural', 'female': 'it-IT-ElsaNeural', 'mymemory_code': 'it-IT'}
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

def get_session_id():
    """Obtiene el ID único de la sesión de Streamlit para el usuario actual."""
    ctx = get_script_run_ctx()
    return ctx.session_id if ctx else "default"

async def generate_audio(text, voice_id, output_file):
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(output_file)

def cleanup_old_audios():
    """Elimina únicamente los audios generados por la sesión del usuario actual."""
    try:
        session_id = get_session_id()
        # Evita borrar archivos de otros usuarios concurrentes
        files = glob.glob(os.path.join(STATIC_DIR, f"traduccion_{session_id}_*.mp3"))
        for f in files:
            if os.path.exists(f):
                os.remove(f)
    except Exception as e:
        print(f"Error al limpiar audios: {e}")

def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    session_id = get_session_id()
    temp_wav = os.path.join(STATIC_DIR, f"temp_{session_id}.wav")
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

# --- FUNCIÓN CALLBACK PARA INTERCAMBIAR IDIOMAS ---
def swap_languages():
    if st.session_state.source_lang != 'auto':
        old_src = st.session_state.source_lang
        st.session_state.source_lang = st.session_state.target_lang
        st.session_state.target_lang = old_src
    else:
        st.toast("⚠️ No puedes intercambiar si está seleccionado 'Detectar idioma'.")

# --- INTERFAZ GRÁFICA ---
st.title("🗣️ Traductor de Texto y Voz")

# Renderizado de selectores de idioma reactivos fuera de formulario
col_src, col_btn, col_tgt = st.columns([4, 2, 4])
src_options = {'auto': 'Detectar idioma', **{k: v['name'] for k, v in VOICE_MAPPING.items()}}

with col_src:
    source_lang = st.selectbox(
        "De:", 
        options=list(src_options.keys()), 
        format_func=lambda x: src_options[x],
        index=list(src_options.keys()).index(st.session_state.source_lang)
    )
    st.session_state.source_lang = source_lang

with col_btn:
    st.write(" ") # Espacio para alinear verticalmente el botón con los selectores
    st.button("🔄", help="Intercambiar idiomas", on_click=swap_languages)

with col_tgt:
    target_lang = st.selectbox(
        "A:", 
        options=list(VOICE_MAPPING.keys()), 
        format_func=lambda x: VOICE_MAPPING[x]['name'],
        index=list(VOICE_MAPPING.keys()).index(st.session_state.target_lang)
    )
    st.session_state.target_lang = target_lang

# Parámetros adicionales
col_engine, col_gender = st.columns(2)
with col_engine:
    translator_engine = st.selectbox("Motor de traducción:", options=["Google Translator", "MyMemory"])
with col_gender:
    voice_gender = st.selectbox("Voz de salida:", options=['female', 'male'], format_func=lambda x: 'Femenina' if x == 'female' else 'Masculina')

st.markdown("### Texto a traducir:")

# Grabador de audio reactivo
audio_file = st.audio_input("Dictar por voz (opcional):")

if audio_file:
    with st.spinner("Transcribiendo..."):
        transcription = transcribe_audio(audio_file)
        if not transcription.startswith("⚠️"):
            st.session_state.text_input = transcription
        else:
            st.error(transcription)

# Editor de texto libre
user_query = st.text_area(
    label="Escribe o edita el texto aquí abajo:",
    value=st.session_state.text_input, 
    placeholder="Tu texto aparecerá aquí si dictás, o podés escribir directamente..."
).strip()

st.session_state.text_input = user_query

# Botón disparador de traducción
submit_button = st.button("Traducir y Escuchar", type="primary")

# --- LÓGICA DE PROCESAMIENTO ---
if submit_button:
    if not user_query:
        st.error("Por favor, ingresa texto o graba un audio primero.")
    else:
        with st.spinner("Traduciendo y generando audio..."):
            try:
                # 1. Limpieza segura de los audios previos de ESTE usuario
                cleanup_old_audios()
                
                # 2. Selección de motor de traducción
                if translator_engine == "Google Translator":
                    st.session_state.translated_text = GoogleTranslator(
                        source=st.session_state.source_lang, 
                        target=st.session_state.target_lang
                    ).translate(user_query)
                else:
                    mymemory_src = VOICE_MAPPING.get(st.session_state.source_lang, {}).get('mymemory_code', 'auto') if st.session_state.source_lang != 'auto' else 'auto'
                    mymemory_tgt = VOICE_MAPPING[st.session_state.target_lang]['mymemory_code']
                    
                    st.session_state.translated_text = MyMemoryTranslator(
                        source=mymemory_src, 
                        target=mymemory_tgt
                    ).translate(user_query)
                
                # 3. Generación del archivo MP3 aislado con Session ID
                selected_voice = VOICE_MAPPING[st.session_state.target_lang][voice_gender]
                session_id = get_session_id()
                unique_id = uuid.uuid4().hex[:6]
                
                st.session_state.audio_filename = f"traduccion_{session_id}_{unique_id}.mp3"
                st.session_state.audio_path = os.path.join(STATIC_DIR, st.session_state.audio_filename)
                
                asyncio.run(generate_audio(st.session_state.translated_text, selected_voice, st.session_state.audio_path))
                
            except Exception as e:
                st.error(f"Error en el proceso: {str(e)}")

# --- BLOQUE DE RESULTADOS ---
if st.session_state.translated_text and st.session_state.audio_path:
    st.write("---") 
    st.success("¡Traducción completada!")
    
    st.subheader("Texto Traducido:")
    st.info(st.session_state.translated_text)
    
    # Inyección de botón "Copiar" compatible mediante st.iframe
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
    st.iframe(js_button, height=45)

    st.subheader("Audio de Salida:")
    st.audio(st.session_state.audio_path, format="audio/mp3")
    
    # Descarga nativa leyendo el archivo del usuario
    with open(st.session_state.audio_path, "rb") as file:
        st.download_button(
            label="📥 Descargar Audio MP3",
            data=file,
            file_name=st.session_state.audio_filename,
            mime="audio/mp3"
        )
