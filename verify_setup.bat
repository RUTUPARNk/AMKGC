@echo off
REM Activate virtual environment and run verification script

echo Activating virtual environment...
call as\Scripts\Activate.bat

echo Running Neo4j setup verification...
python verify_neo4j_setup.py

echo.
pause
