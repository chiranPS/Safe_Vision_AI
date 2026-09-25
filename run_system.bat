@echo off
echo Starting Backend...
start cmd.exe /k "cd backend && npm.cmd run dev"

echo Starting Frontend...
start cmd.exe /k "npm.cmd run dev"

echo Starting AI Service...
start cmd.exe /k "cd ai-service && .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

echo System is starting up in separate windows!

