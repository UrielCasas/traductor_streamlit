@echo off
set DIRECTORIO_ACTUAL = "%~d0%~p0"
cd %DIRECTORIO_ACTUAL%
@PROMPT $P$_$$$S
start python app.py
