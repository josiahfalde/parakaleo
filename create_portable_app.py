
import shutil
import os
import subprocess
import sys

def create_portable_app():
    """Create a portable app that users can download and run"""
    
    # Create portable app directory
    app_dir = "ParakaleoMed_Portable"
    if os.path.exists(app_dir):
        shutil.rmtree(app_dir)
    
    os.makedirs(app_dir)
    
    # Copy all necessary files
    files_to_copy = [
        "app.py",
        "attached_assets",
        ".streamlit",
        "pyproject.toml"
    ]
    
    for item in files_to_copy:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.copytree(item, os.path.join(app_dir, item))
            else:
                shutil.copy2(item, app_dir)
    
    # Create startup batch file for Windows
    with open(os.path.join(app_dir, "Start_ParakaleoMed.bat"), "w") as f:
        f.write("""@echo off
echo Starting ParakaleoMed...
python -m streamlit run app.py --server.port 8501 --server.headless true
pause
""")
    
    # Create startup script for Mac/Linux
    with open(os.path.join(app_dir, "start_parakaleomd.sh"), "w") as f:
        f.write("""#!/bin/bash
echo "Starting ParakaleoMed..."
python3 -m streamlit run app.py --server.port 8501 --server.headless true
""")
    
    # Make shell script executable
    os.chmod(os.path.join(app_dir, "start_parakaleomd.sh"), 0o755)
    
    # Create README
    with open(os.path.join(app_dir, "README.txt"), "w") as f:
        f.write("""ParakaleoMed - Portable Medical Clinic App

REQUIREMENTS:
- Python 3.11 or newer must be installed
- Internet connection for first-time setup only

WINDOWS USERS:
1. Double-click "Start_ParakaleoMed.bat"
2. Wait for the app to start
3. Your browser will open automatically

MAC/LINUX USERS:
1. Open Terminal in this folder
2. Run: ./start_parakaleomd.sh
3. Open browser to: http://localhost:8501

The app works completely offline after setup!
All patient data is stored locally on your device.
""")
    
    print(f"Portable app created in {app_dir}/")
    print("Zip this folder and share it - no app store needed!")

if __name__ == "__main__":
    create_portable_app()
