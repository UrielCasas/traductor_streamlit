# **Traductor - Large Language Model**
Un modelo de lenguaje a gran escala con una interfaz para poder interactuar con la misma, y realizada para presentar como trabajo final en la materia _Técnicas de Procesamiento del Habla_.

La app solamente esta desplegado en _Streamlit_ para poder interactuar con el LLM basado en los motores de _Google Translator_ (de Google) y MyMemory (de Microsoft).

## 🏗️ **Estructura del Proyecto**
```text
.
├── .devcontainer/
│   └── devcontainer.json   # Utilizada por Streamlit para crear la interfaz
│
├── static/                 # Se agregan los archivos .mp3 en esta carpeta
│
├── tests/                  # Experimentación y análisis de los modelos
│   ├── videos/
│   │    └── Video del LLM como experimentación
│   ├── texto_corto.md
│   └── texto_largo.md
│
├── versiones/              # Archivos .py sobre la evolución del LLM
│
├── README.md               # Información sobre el repositorio
├── app.py                  # Archivo de python donde se encuentra el LLM
├── instalar.bat            # Instala las librerias de requirements.txt
└── requirements.txt        # Requisitos (librerias) para utilizar el LLM
```

## 🛫 **Deployment del LLM**

Enlace a la app desplegada en Streamlit: https://traductortph.streamlit.app/

## 🛠️ Herramientas

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://docs.python.org/es/3/)
[![edge-tts](https://img.shields.io/badge/edge--tts-0078D4?style=flat&logo=microsoftedge&logoColor=white)](https://pypi.org/project/edge-tts/)
[![deep-translator](https://img.shields.io/badge/deep--translator-4285F4?style=flat&logo=googletranslate&logoColor=white)](https://deep-translator.readthedocs.io/en/latest/)
[![SpeechRecognition](https://img.shields.io/badge/SpeechRecognition-3776AB?style=flat\&logo=python\&logoColor=white)](https://pypi.org/project/SpeechRecognition/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat\&logo=streamlit\&logoColor=white)](https://streamlit.io/)
[![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=flat\&logo=googlegemini\&logoColor=white)](https://gemini.google.com/)
<!--
[![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/en/stable/)
[![os](https://img.shields.io/badge/os-3776AB?style=flat\&logo=python\&logoColor=white)](https://docs.python.org/es/3/library/os.html)
[![asyncio](https://img.shields.io/badge/asyncio-3776AB?style=flat&logo=python&logoColor=white)](https://docs.python.org/es/3/library/asyncio.html)
[![uuid](https://img.shields.io/badge/uuid-3776AB?style=flat&logo=python&logoColor=white)](https://docs.python.org/es/3/library/uuid.html)
[![glob](https://img.shields.io/badge/glob-3776AB?style=flat&logo=python&logoColor=white)](https://docs.python.org/3/library/glob.html)
-->

## 👥 **Autores**
- Arnaldo Antonio Fustet
- Uriel Maximiano Casas

