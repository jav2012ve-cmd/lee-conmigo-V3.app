@echo off
setlocal

cd /d "%~dp0"

echo Iniciando LeeConmigo DEMO...
start "" "http://localhost:8501"
python -m streamlit run main_DEMO.py

endlocal
