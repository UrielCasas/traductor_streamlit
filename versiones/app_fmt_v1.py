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

# --- CONFIGURACIÓN DE PÁGINA Y ESTILOS MODERNOS ---
st.set_page_config(
    page_title="Traductor Inteligente Pro", 
    page_icon="🗣️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inyección de CSS de vanguardia para tunear la interfaz nativa de Streamlit
st.markdown("""
    <style>
        /* Tipografía general y suavizado */
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Contenedor principal de traducción */
        .translation-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(8px);
        }
        
        /* Botón de intercambio estilizado */
        div[data-testid="stColumn"]:nth-child(2) button {
            background-color: #262730 !important;
            border: 1px solid #4A4B57 !important;
            border-radius: 50% !important;
            width: 45px !important;
            height: 45px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 24px auto 0 auto !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stColumn"]:nth-child(2) button:hover {
            border-color: #FF4B4B !important;
            transform: rotate(180deg);
            box-shadow: 0 0 12px rgba(255, 75, 75, 0.4);
        }
        
        /* Estilos específicos para las cajas de texto */
        textarea {
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            font-size: 16px !important;
            line-height: 1.6 !important;
        }
        
        /* Ocultar elementos innecesarios de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

STATIC_DIR = 'static'
os.makedirs(STATIC_DIR, exist_ok=True)

VOICE_MAPPING = {
    'en': {'name': '🇬🇧 Inglés', 'male': 'en-US-BrianNeural', 'female': 'en-US-EmmaNeural', 'mymemory_code': 'en-US'},
    'es': {'name': '🇪🇸 Español', 'male': 'es-AR-TomasNeural', 'female': 'es-MX-DaliaNeural', 'mymemory_code': 'es-AR'},
    'fr': {'name': '🇫🇷 Francés', 'male': 'fr-FR-RemyNeural', 'female': 'fr-FR-DeniseNeural', 'mymemory_code': 'fr-FR'},
    'de': {'name': '🇩🇪 Alemán', 'male': 'de-DE-ConradNeural', 'female': 'de-DE-AmalaNeural', 'mymemory_code': 'de-DE'},
    'pt': {'name': '🇧🇷 Portugués', 'male': 'pt-BR-AntonioNeural', 'female': 'pt-BR-FranciscaNeural', 'mymemory_code': 'pt-PT'},
    'it': {'name': '🇮🇹 Italiano', 'male': 'it-IT-DiegoNeural', 'female': 'it-IT-ElsaNeural', 'mymemory_code': 'it-IT'}
}

# --- SISTEMA DE LIMPIEZA DE ARCHIVOS HUÉRFANOS ---
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
            print(f"Error en el limpiador en segundo plano: {e}")
        time.sleep(interval_seconds)

if "cleaner_started" not in st.session_state:
    @st.cache_resource
    def start_cleaner_thread():
        thread = Thread(target=background_cleaner, daemon=True)
        thread.start()
        return True
    
    start_cleaner_thread()
    st.session_state.cleaner_started = True

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

def swap_languages():
    if st.session_state.source_lang != 'auto':
        old_src = st.session_state.source_lang
        st.session_state.source_lang = st.session_state.target_lang
        st.session_state.target_lang = old_src
    else:
        st.toast("⚠️ No puedes intercambiar si está seleccionado 'Detectar idioma'.")

# --- ENTORNO GRÁFICO REDISEÑADO ---

# Encabezado minimalista
st.markdown("<h1 style='text-align: center; font-weight: 800; margin-bottom: 5px;'>🗣️ Traductor Inteligente</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8A8B94; margin-bottom: 30px;'>Dictá, escribí y traducí al instante con voz artificial avanzada</p>", unsafe_allow_html=True)

# BARRA LATERAL (Sidebar) para configuraciones secundarias, dejando la pantalla limpia
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    translator_engine = st.selectbox("Motor del traductor:", options=["Google Translator", "MyMemory"])
    voice_gender = st.selectbox("Género de la voz:", options=['female', 'male'], format_func=lambda x: 'Femenina' if x == 'female' else 'Masculina')
    st.write("---")
    st.caption("Traductor Pro v2.5")

# Sección de selectores principales usando columnas asimétricas corregidas para estética [4, 1.5, 4]
col_src, col_btn, col_tgt = st.columns([4, 1.5, 4])
src_options = {'auto': '🔍 Detectar idioma', **{k: v['name'] for k, v in VOICE_MAPPING.items()}}

with col_src:
    source_lang = st.selectbox("De:", options=list(src_options.keys()), format_func=lambda x: src_options[x], index=list(src_options.keys()).index(st.session_state.source_lang), label_visibility="collapsed")
    st.session_state.source_lang = source_lang

with col_btn:
    st.button("🔄", help="Intercambiar idiomas", on_click=swap_languages)

with col_tgt:
    target_lang = st.selectbox("A:", options=list(VOICE_MAPPING.keys()), format_func=lambda x: VOICE_MAPPING[x]['name'], index=list(VOICE_MAPPING.keys()).index(st.session_state.target_lang), label_visibility="collapsed")
    st.session_state.target_lang = target_lang

# Panel Principal de Entrada de Datos envuelto en un contenedor visual estético
st.markdown('<div class="translation-card">', unsafe_allow_html=True)

audio_file = st.audio_input("Dictar por voz (opcional):")

if audio_file:
    with st.spinner("Transcribiendo audio..."):
        transcription = transcribe_audio(audio_file)
        if not transcription.startswith("⚠️"):
            st.session_state.text_input = transcription
        else:
            st.error(transcription)

user_query = st.text_area(
    label="Texto original:",
    value=st.session_state.text_input, 
    placeholder="Escribí lo que quieras acá o activá el micrófono de arriba...",
    height=140,
    label_visibility="collapsed"
).strip()

st.session_state.text_input = user_query
st.markdown('</div>', unsafe_allow_html=True)

# Botón de acción principal centrado y destacado
col_center, _ = st.columns([2, 1])
with col_center:
    submit_button = st.button("Traducir y Escuchar 🚀", type="primary", use_container_width=True)

# --- LÓGICA DE PROCESAMIENTO ---
if submit_button:
    if not user_query:
        st.toast("⚠️ Por favor, ingresá texto primero.")
    else:
        with st.spinner("Procesando traducción y síntesis de voz..."):
            try:
                cleanup_old_audios()
                
                if translator_engine == "Google Translator":
                    st.session_state.translated_text = GoogleTranslator(source=st.session_state.source_lang, target=st.session_state.target_lang).translate(user_query)
                else:
                    mymemory_src = VOICE_MAPPING.get(st.session_state.source_lang, {}).get('mymemory_code', 'auto') if st.session_state.source_lang != 'auto' else 'auto'
                    mymemory_tgt = VOICE_MAPPING[st.session_state.target_lang]['mymemory_code']
                    st.session_state.translated_text = MyMemoryTranslator(source=mymemory_src, target=mymemory_tgt).translate(user_query)
                
                # 3. Generación del archivo MP3 aislado con Session ID
                selected_voice = VOICE_MAPPING[st.session_state.target_lang][voice_gender]
                session_id = get_session_id()
                unique_id = uuid.uuid4().hex[:6]
                
                st.session_state.audio_filename = f"traduccion_{session_id}_{unique_id}.mp3"
                st.session_state.audio_path = os.path.join(STATIC_DIR, st.session_state.audio_filename)
                
                asyncio.run(generate_audio(st.session_state.translated_text, selected_voice, st.session_state.audio_path))
                
            except Exception as e:
                st.error(f"Error en el proceso: {str(e)}")

# --- BLOQUE DE RESULTADOS REDISEÑADO ---
if st.session_state.translated_text and st.session_state.audio_path:
    st.markdown("<br><h4 style='font-weight: 700;'>Resultado de la traducción:</h4>", unsafe_allow_html=True)
    
    # Contenedor visual para la respuesta de salida
    st.markdown('<div class="translation-card" style="background: rgba(76, 175, 80, 0.05); border-color: rgba(76, 175, 80, 0.2);">', unsafe_allow_html=True)
    st.info(st.session_state.translated_text)
    
    # Copiar texto interactivo mediante iframe personalizado
    js_button = f"""
    <script>
    function copyText() {{
        navigator.clipboard.writeText(`{st.session_state.translated_text}`);
        alert("¡Texto copiado al portapapeles!");
    }}
    </script>
    <button onclick="copyText()" style="
        background-color: #262730; 
        color: #E6E6E6; 
        border: 1px solid #4A4B57; 
        padding: 8px 16px; 
        border-radius: 8px; 
        cursor: pointer;
        font-family: sans-serif;
        font-weight: 500;
        transition: background 0.2s;">
        📋 Copiar Texto Traducido
    </button>
    """
    st.iframe(js_button, height=45)
    
    st.markdown("##### 🔉 Escuchar Audio:")
    st.audio(st.session_state.audio_path, format="audio/mp3")
    
    # Descarga limpia del archivo generado
    with open(st.session_state.audio_path, "rb") as file:
        st.download_button(
            label="📥 Descargar Audio MP3",
            data=file,
            file_name=st.session_state.audio_filename,
            mime="audio/mp3",
            use_container_width=True
        )
    st.markdown('</div>', unsafe_allow_html=True)
