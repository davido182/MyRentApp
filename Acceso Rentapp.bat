@echo off
call C:\Users\Issues\miniconda3\Scripts\activate.bat
call conda activate suites_env
echo Iniciando la aplicación Suites...
streamlit run Rentapp.py
pause
