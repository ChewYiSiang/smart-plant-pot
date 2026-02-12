import sys
import os
import socket
import importlib.util

def report(msg):
    with open("env_report.txt", "a") as f:
        f.write(msg + "\n")

def check_env():
    if os.path.exists("env_report.txt"): os.remove("env_report.txt")
    report("--- Environment Audit ---")
    report(f"Python Version: {sys.version}")
    
    # Check dependencies
    for pkg in ["fastapi", "uvicorn", "pydantic", "sqlmodel", "google.cloud.texttospeech"]:
        try:
            importlib.import_module(pkg.split('.')[0])
            report(f"Package {pkg}: INSTALLED")
        except ImportError:
            report(f"Package {pkg}: MISSING")
            
    # Check port 8000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 8000))
        report("Port 8000: AVAILABLE")
        s.close()
    except Exception as e:
        report(f"Port 8000: BLOCKED/IN USE - {e}")

    # Check main.py syntax
    try:
        import main
        report("main.py: IMPORT SUCCESSFUL")
    except Exception as e:
        import traceback
        report(f"main.py: IMPORT FAILED - {e}")
        report(traceback.format_exc())

if __name__ == "__main__":
    check_env()
