# **Traductor - Large Language Model**
Un modelo de lenguaje a gran escala con una interfaz para poder interactuar con la misma, y realizada para presentar como trabajo final en la materia _Técnicas de Procesamiento del Habla_.

# 🏗️ **Estructura del Proyecto**
```text
.
├── pruebas/
│   └── pruebas.md
│   └── Experimentación y análisis
│
├── static/
│   └── Se agregan los archivos .mp3 en esta carpeta
│
├── DEPLOY.md             # Instrucciones para desplegar la app
├── README.md             # Información sobre este repositorio
├── app.py                # Archivo de python para activar el LLM
├── ejecutar.bat          # Ejecuta este archivo
├── index.html            # Página principal con los estilos aplicados
└── requirements.txt      # Requisitos para utilizar el LLM
```

# 🛫 **Deployment del LLM**

1) Utilizar _pip install -r requirements.txt_ para instalar los requisitos necesarios

2) Doble click en: _ejecutar.bat_
   - Si aparece el mensaje:
      * _Serving Flask app 'app'_
      * _Debug mode: off_
      * _WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead._
      * _Running on http://127.0.0.1:5000_
      * _Press CTRL+C to quit_
   - Está funcionando el servidor

3) Abrir el navegador e ir al sitio: _localhost:5000_

## 🛠️ Herramientas

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://docs.python.org/es/3/)
[![edge-tts](https://img.shields.io/badge/edge--tts-0078D4?style=flat&logo=microsoftedge&logoColor=white)](https://pypi.org/project/edge-tts/)
[![deep-translator](https://img.shields.io/badge/deep--translator-4285F4?style=flat&logo=googletranslate&logoColor=white)](https://deep-translator.readthedocs.io/en/latest/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/en/stable/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat\&logo=streamlit\&logoColor=white)](https://streamlit.io/)
[![os](https://img.shields.io/badge/os-3776AB?style=flat\&logo=python\&logoColor=white)](https://docs.python.org/es/3/library/os.html)
[![asyncio](https://img.shields.io/badge/asyncio-3776AB?style=flat&logo=python&logoColor=white)](https://docs.python.org/es/3/library/asyncio.html)
[![uuid](https://img.shields.io/badge/uuid-3776AB?style=flat&logo=python&logoColor=white)](https://docs.python.org/es/3/library/uuid.html)
[![glob](https://img.shields.io/badge/glob-3776AB?style=flat&logo=python&logoColor=white)](https://docs.python.org/3/library/glob.html)
[![SpeechRecognition](https://img.shields.io/badge/SpeechRecognition-3776AB?style=flat\&logo=python\&logoColor=white)](https://pypi.org/project/SpeechRecognition/)


# 👥 **Autores**
- Arnaldo Antonio Fustet
- Uriel Maximiano Casas

