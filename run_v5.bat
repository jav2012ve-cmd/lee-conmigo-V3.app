@echo off
setlocal

cd /d "%~dp0"

echo Iniciando LeeConmigo 5.0 ^(base lee_conmigo_v5.db^)...
start "" "http://localhost:8501"
python -m streamlit run main_V5.py

endlocal
