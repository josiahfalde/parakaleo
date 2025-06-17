
import subprocess
import sys
import os

def create_executable():
    """Create a standalone executable of the ParakaleoMed app"""
    
    # Install PyInstaller if not already installed
    try:
        import PyInstaller
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create the executable
    command = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "ParakaleoMed",
        "--add-data", "attached_assets;attached_assets",
        "--add-data", ".streamlit;.streamlit", 
        "--hidden-import", "streamlit.web.cli",
        "--hidden-import", "sqlite3",
        "--hidden-import", "pandas",
        "app.py"
    ]
    
    subprocess.run(command)
    print("Executable created in dist/ParakaleoMed.exe")
    print("Users can download this file and run it directly - no installation needed!")

if __name__ == "__main__":
    create_executable()
