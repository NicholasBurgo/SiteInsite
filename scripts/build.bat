@echo off
echo Building SiteInsite...

REM Setup virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    py -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

echo Building FastAPI backend...
cd backend
pip install -q -r requirements.txt
cd ..

echo Building React frontend...
cd frontend
npm install
npm run build
cd ..

echo Build complete!
echo To start production:
echo   Backend: call venv\Scripts\activate && cd backend && uvicorn backend.app:app --port 5051
echo   Frontend: cd frontend && npm run preview

pause