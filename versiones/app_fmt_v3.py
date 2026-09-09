import os
import asyncio
import uuid
import glob
import time
from threading import Thread
import streamlit as st
import edge_tts
from deep_translator import GoogleTranslator, MyMemoryTranslator
import speech_recognition as sr
from streamlit.runtime.scriptrunner import get_script_run_ctx

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Traductor Inteligente", 
    page_icon="🗣️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- INICIALIZACIÓN DEL ESTADO DE SESIÓN ---
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'dark'  # Arranca por defecto en modo oscuro
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

# --- INYECCIÓN DE CSS SEGURO Y DINÁMICO ---
bg_app = "#1E1F25" if st.session_state.theme_mode == 'dark' else "#F8F9FA"
text_color = "#FFFFFF" if st.session_state.theme_mode == 'dark' else "#121212"
btn_label = "Modo Claro ☀️" if st.session_state.theme_mode == 'dark' else "Modo Oscuro 🌙"

st.markdown(f"""
    <style>
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 580px !important;
        }}
        html, body, [data-testid="stAppViewContainer"] {{
            background-color: {bg_app} !important;
            color: {text_color} !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .section-label {{
            font-weight: 700;
            font-size: 14px;
            margin-bottom: 6px;
            margin-top: 12px;
            color: {text_color};
        }}
        /* Alinear verticalmente el botón de intercambio nativo */
        div[data-testid="stColumn"]:nth-child(2) button {{
            margin-top: 28px !important;
            height: 42px !important;
            width: 100% !important;
            background-color: #31333F !important;
            border: 1px solid #4A4B57 !important;
        }}
        /* Forzar que los radio buttons de Streamlit se vean limpios */
        div[data-testid="stRadio"] div[role="radiogroup"] {{
            gap: 15px;
        }}
        #MainMenu, footer, header {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

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

# --- SISTEMA DE LIMPIEZA EN SEGUNDO PLANO ---
def background_cleaner(interval_seconds=600, max_age_seconds=1800):
    while True:
        try:
            now = time.time()
            for pattern in ["traduccion_*.mp3", "temp_*.wav"]:
                files = glob.glob(os.path.join(STATIC_DIR, pattern))
                for f in files:
                    if os.path.exists(f):
                        if now - os.path.getmtime(f) > max_age_seconds:
                            os.remove(f)
        except Exception as e:
            print(f"Error en el limpiador: {e}")
        time.sleep(interval_seconds)

if "cleaner_started" not in st.session_state:
    @st.cache_resource
    def start_cleaner_thread():
        thread = Thread(target=background_cleaner, daemon=True)
        thread.start()
        return True
    start_cleaner_thread()
    st.session_state.cleaner_started = True

# --- FUNCIONES DE CONTROL ---
def toggle_theme():
    st.session_state.theme_mode = 'light' if st.session_state.theme_mode == 'dark' else 'dark'

def get_session_id():
    ctx = get_script_run_ctx()
    return ctx.session_id if ctx else "default"

async def generate_audio(text, voice_id, output_file):
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(output_file)

def cleanup_old_audios():
    try:
        session_id = get_session_id()
        files = glob.glob(os.path.join(STATIC_DIR, f"traduccion_{session_id}_*.mp3"))
        for f in files:
            if os.path.exists(f):
                os.remove(f)
    except Exception as e:
        print(f"Error al limpiar: {e}")

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
            return r.recognize_google(audio_data, language=lang_code)
    except Exception:
        return "⚠️ No se pudo procesar la voz."
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

def swap_languages():
    if st.session_state.source_lang != 'auto':
        old_src = st.session_state.source_lang
        st.session_state.source_lang = st.session_state.target_lang
        st.session_state.target_lang = old_src
    else:
        st.toast("⚠️ No puedes intercambiar en modo automático.")

# --- INTERFAZ GRÁFICA ESTABILIZADA ---

col_space, col_theme = st.columns([7, 3])
with col_theme:
    st.button(btn_label, on_click=toggle_theme, use_container_width=True)

st.markdown("<h2 style='text-align: center; font-weight: 700; margin-top: -10px;'>Traductor Inteligente</h2>", unsafe_allow_html=True)

# Selectores de Idioma
col_de, col_inter, col_a = st.columns([4.5, 1, 4.5])
with col_de:
    st.markdown('<p class="section-label">De:</p>', unsafe_allow_html=True)
    src_options = {'auto': 'Detectar idioma ✨', **{k: v['name'] for k, v in VOICE_MAPPING.items()}}
    source_lang = st.selectbox("De:", options=list(src_options.keys()), format_func=lambda x: src_options[x], index=list(src_options.keys()).index(st.session_state.source_lang), label_visibility="collapsed")
    st.session_state.source_lang = source_lang

with col_inter:
    st.button("⇆", on_click=swap_languages, use_container_width=True)

with col_a:
    st.markdown('<p class="section-label">A:</p>', unsafe_allow_html=True)
    target_lang = st.selectbox("A:", options=list(VOICE_MAPPING.keys()), format_func=lambda x: VOICE_MAPPING[x]['name'], index=list(VOICE_MAPPING.keys()).index(st.session_state.target_lang), label_visibility="collapsed")
    st.session_state.target_lang = target_lang

# Entrada de Texto y Grabador de voz
st.markdown('<p class="section-label">Texto a traducir / Dictar:</p>', unsafe_allow_html=True)
col_txt, col_mic = st.columns([8.2, 1.8])

with col_mic:
    audio_file = st.audio_input("Dictar", label_visibility="collapsed")
    if audio_file:
        with st.spinner(""):
            transcription = transcribe_audio(audio_file)
            if not transcription.startswith("⚠️"):
                st.session_state.text_input = transcription

with col_txt:
    user_query = st.text_area(label="Txt", value=st.session_state.text_input, placeholder="Escribe algo aquí...", height=100, label_visibility="collapsed").strip()
    st.session_state.text_input = user_query

# Opciones Inferiores (Voz del Audio / Motor de Traducción)
col_v, col_m = st.columns(2)
with col_v:
    st.markdown('<p class="section-label">Voz del Audio:</p>', unsafe_allow_html=True)
    voice_gender = st.selectbox("Voz:", options=['female', 'male'], format_func=lambda x: 'Femenina' if x == 'female' else 'Masculina', label_visibility="collapsed")

with col_m:
    st.markdown('<p class="section-label">Motor:</p>', unsafe_allow_html=True)
    # st.radio horizontal con index=0 para que aparezca seleccionado por defecto de forma segura
    translator_engine = st.radio("Motor:", options=["Google Translator", "MyMemory"], index=0, horizontal=True, label_visibility="collapsed")

# --- BOTONERA INFERIOR COMPACTA PERFECTAMENTE ALINEADA ---
st.write("")
col_borrar, col_traducir = st.columns(2) # ([3.5, 6.5])

with col_borrar:
    btn_borrar = st.button("Borrar", use_container_width=True)
    if btn_borrar:
        st.session_state.text_input = ''
        st.session_state.translated_text = None
        cleanup_old_audios()
        st.session_state.audio_path = None
        st.rerun()

with col_traducir:
    submit_button = st.button("Traducir", type="primary", use_container_width=True)

# --- PROCESAMIENTO DE TRADUCCIÓN ---
if submit_button:
    if not user_query:
        st.toast("⚠️ Por favor, ingresa texto primero.")
    else:
        try:
            cleanup_old_audios()
            if translator_engine == "Google Translator":
                st.session_state.translated_text = GoogleTranslator(source=st.session_state.source_lang, target=st.session_state.target_lang).translate(user_query)
            else:
                mymemory_src = VOICE_MAPPING.get(st.session_state.source_lang, {}).get('mymemory_code', 'auto') if st.session_state.source_lang != 'auto' else 'auto'
                mymemory_tgt = VOICE_MAPPING[st.session_state.target_lang]['mymemory_code']
                st.session_state.translated_text = MyMemoryTranslator(source=mymemory_src, target=mymemory_tgt).translate(user_query)
            
            selected_voice = VOICE_MAPPING[st.session_state.target_lang][voice_gender]
            session_id = get_session_id()
            unique_id = uuid.uuid4().hex[:6]
            st.session_state.audio_filename = f"traduccion_{session_id}_{unique_id}.mp3"
            st.session_state.audio_path = os.path.join(STATIC_DIR, st.session_state.audio_filename)
            
            asyncio.run(generate_audio(st.session_state.translated_text, selected_voice, st.session_state.audio_path))
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Bloque "Resultado"
st.markdown('<p class="section-label">Resultado:</p>', unsafe_allow_html=True)
if st.session_state.translated_text:
    st.info(st.session_state.translated_text)
    st.audio(st.session_state.audio_path, format="audio/mp3")
    
    col_dl, col_cp = st.columns([1, 1])  # Se le pasa explícitamente [1, 1] para evitar el TypeError
    with col_dl:
        with open(st.session_state.audio_path, "rb") as file:
            st.download_button(label="📥 Descargar MP3", data=file, file_name=st.session_state.audio_filename, mime="audio/mp3", use_container_width=True)
    with col_cp:
        js_button = f"""
        <script>
        function copyText() {{ navigator.clipboard.writeText(`{st.session_state.translated_text}`); alert("¡Texto copiado!"); }}
        </script>
        <button onclick="copyText()" style="background-color: #31333F; color: white; border: 1px solid #4A4B57; padding: 6px 16px; border-radius: 6px; cursor: pointer; width:100%; height:38px; font-family:sans-serif; font-size:14px;">📋 Copiar Texto</button>
        """
        st.iframe(js_button, height=45)
else:
    st.text_area(label="Resultado inactivo:", value="", placeholder="La traducción aparecerá aquí...", height=70, label_visibility="collapsed", disabled=True)
