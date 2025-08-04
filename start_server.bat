@echo off
echo Starting Enhanced PDF Converter API...
echo.

REM Check if venv exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found, using system Python...
)

REM Try different Python commands
if exist "python.exe" (
    echo Using local python.exe...
    python.exe app.py
) else if exist "py" (
    echo Using py launcher...
    py app.py
) else (
    echo Starting with python command...
    python app.py
)

pause 