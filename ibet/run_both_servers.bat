@echo off
echo Starting Django Backend Server...
start "Django Server" cmd /k "cd /d c:\Users\user\Documents\IBET\ibet && call c:\Users\user\Documents\IBET\venv\Scripts\activate.bat && python manage.py runserver 8000"

echo Waiting for Django to start...
timeout /t 5 /nobreak > nul

echo Starting React Frontend Server...
start "React Server" cmd /k "cd /d c:\Users\user\Documents\IBET\ibet\frontend && npm run dev"

echo Both servers are starting!
echo - Django: http://localhost:8000
echo - React: http://localhost:5173
pause
