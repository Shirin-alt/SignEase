@echo off
call .venv\Scripts\activate.bat
python -m pip install flask-cors
python app.py
