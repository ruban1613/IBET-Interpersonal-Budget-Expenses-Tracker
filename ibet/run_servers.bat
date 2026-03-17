@echo off
cd /d "c:\Users\user\Documents\IBET\ibet"
call "c:\Users\user\Documents\IBET\venv\Scripts\activate.bat"
python manage.py runserver 8000
