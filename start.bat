@echo off
title LUPTIFY Music Server
echo Starting LUPTIFY Music Server v2.0...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
) else (
    python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
)
pause
