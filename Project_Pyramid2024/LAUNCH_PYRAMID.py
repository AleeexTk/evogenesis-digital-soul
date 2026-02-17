import os
import sys
import subprocess
import time
import webbrowser
import threading

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, color=RESET):
    print(f"{color}[LAUNCHER] {msg}{RESET}")

def install_dependencies():
    log("Checking Python dependencies...", YELLOW)
    required = ["fastapi", "uvicorn", "click", "pyyaml", "requests"]
    
    # 0. Ensure PIP exists
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("PIP not found. Attempting to install PIP via ensurepip...", YELLOW)
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
            log("PIP installed successfully.", GREEN)
        except Exception as e:
            log(f"CRITICAL: Could not install PIP. Error: {e}", RED)
            log("Please install Python correctly or use a global interpreter.", RED)
            sys.exit(1)

    # 1. Install Packages (Standard)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + required)
    except subprocess.CalledProcessError:
        log("Standard install failed.", RED)

    # 2. Verify Imports & Force Reinstall if broken
    log("Verifying imports...", YELLOW)
    try:
        # Try to import critical modules to check for corruption
        subprocess.check_call([sys.executable, "-c", "import click.core; import uvicorn; import fastapi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("Dependencies verified.", GREEN)
    except subprocess.CalledProcessError:
        log("Detected corrupted dependencies (e.g. click.core). Force reinstalling...", RED)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-cache-dir", "click", "uvicorn", "fastapi"])
            log("Re-installation complete.", GREEN)
        except subprocess.CalledProcessError:
             log("CRITICAL: Failed to force reinstall dependencies.", RED)
             sys.exit(1)

def run_node_server():
    log("Starting Node.js Frontend (Trailblazer)...", YELLOW)
    # Check if node is available
    try:
        subprocess.Popen(["node", "server.js"], shell=True)
    except FileNotFoundError:
        log("Node.js not found! Please install Node.js.", RED)

def run_python_bridge():
    log("Starting Python Bridge (Purple/Aegis)...", YELLOW)
    # Run bridge_core.py using the current python interpreter
    bridge_path = os.path.join("PURPLE", "bridge_core.py")
    subprocess.Popen([sys.executable, bridge_path])

def main():
    log("=== EVO PYRAMID LAUNCH SEQUENCE ===", GREEN)
    
    # 1. Install Deps
    install_dependencies()
    
    # 2. Start Servers
    run_node_server()
    time.sleep(2) # Give Node a moment
    
    run_python_bridge()
    time.sleep(4) # Give FastAPI a moment
    
    # 3. Open Browser
    url = "http://localhost:3000"
    log(f"Opening Portal: {url}", GREEN)
    webbrowser.open(url)
    
    log("System Online. Press Ctrl+C to stop.", GREEN)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Shutting down...", RED)
        # We rely on the user closing the terminal windows for now, 
        # or we could implement more complex process killing.

if __name__ == "__main__":
    main()
