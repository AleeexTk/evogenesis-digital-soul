import sys
import os
from fastapi.routing import APIRoute

# Add PURPLE to path
sys.path.append(os.path.abspath("PURPLE"))

try:
    from bridge_core import app
    print("\n[DEBUG] Listing all registered routes in bridge_core.app:")
    found_memory = False
    found_core = False
    
    for route in app.routes:
        if isinstance(route, APIRoute):
            print(f"  - {route.path} [{','.join(route.methods)}]")
            if route.path == "/memory":
                found_memory = True
            if route.path == "/core/state":
                found_core = True
                
    print("\n[DEBUG] Analysis:")
    print(f"  - /memory route found: {found_memory}")
    print(f"  - /core/state route found: {found_core}")

except ImportError as e:
    print(f"[ERROR] Could not import bridge_core: {e}")
except Exception as e:
    print(f"[ERROR] Logic error: {e}")
