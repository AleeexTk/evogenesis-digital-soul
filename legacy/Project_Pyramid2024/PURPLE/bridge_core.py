import sys
import os
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime

# Add root to sys.path to allow imports from PROVOCATEUR and SOUL
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PROVOCATEUR.AEGIS.core.policy_engine import PolicyEngine, DecisionAction
from PROVOCATEUR.AEGIS.core.event_tap import EventTap
from PROVOCATEUR.AEGIS.core.deduplication_engine import DeduplicationEngine
from PROVOCATEUR.AEGIS.core.wallet_manager import WalletManager

# Import SOUL Memory
from SOUL.memory_manager import soul_memory

# Import CORE Orchestrator
from CORE.orchestrator import core

# --- Configuration ---
app = FastAPI(title="Purple Bridge", version="1.0.0")
HOST = "127.0.0.1"
PORT = 8000

# AEGIS Initialization
# Ensure paths are correct relative to where the script is run
AEGIS_DIR = os.path.join(os.path.dirname(__file__), '..', 'PROVOCATEUR', 'AEGIS')
event_tap = EventTap(ndjson_path=os.path.join(AEGIS_DIR, "security.ndjson"))
policy_engine = PolicyEngine(config_path=os.path.join(AEGIS_DIR, "security_policies.yaml"))
dedup_engine = DeduplicationEngine(window_size=50, ttl_seconds=300)
wallet_manager = WalletManager(initial_balance=100.0, trust_threshold=0.3)

# CORS - Allow requests from Node.js server (if acting as proxy) or direct browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---
class GenesisProtocolUpdate(BaseModel):
    genesis_meta: Dict[str, Any]
    modules: Dict[str, Any]
    ecosystem: Optional[Dict[str, Any]] = None

class MemoryItem(BaseModel):
    key: str
    value: str
    type: str = "short_term"

# --- Middleware / Dependency ---
async def verify_aegis(request: Request):
    """
    AEGIS Gatekeeper: Intercepts every request and evaluates against security policies.
    """
    method = request.method
    url = str(request.url)
    
    # Context Construction
    # In a real scenario, we'd extract user_id from JWT headers
    user_id = request.headers.get("x-user-id", "anonymous")
    trust_level_header = request.headers.get("x-trust-level", "0.0")
    try:
        trust_level = float(trust_level_header)
    except ValueError:
        trust_level = 0.0
        
    intent = request.headers.get("x-intent", "api_access")

    ctx = {
        "origin": "http",
        "provider": "purple_bridge",
        "method": method,
        "url": url,
        "intent": intent,
        "user_id": user_id,
        "trust_level": trust_level,
        "state": core.state
    }

    # Deduplication / Loop Detection
    loop_count = dedup_engine.check_and_record(ctx)
    ctx["loop_count"] = loop_count

    # Wallet & Trust Integration
    wallet_status = wallet_manager.get_status(user_id=user_id)
    ctx["wallet_balance"] = wallet_status["balance"]
    ctx["is_frozen"] = wallet_status["is_frozen"]

    # Policy Evaluation
    decision = policy_engine.evaluate(ctx)

    # Log Event
    event_tap.log_simple(
        origin="api",
        intent=intent,
        status=decision.action.value,
        details=f"{method} {url} | User: {user_id} | Reason: {decision.reason}"
    )

    if decision.action == DecisionAction.DENY:
        raise HTTPException(status_code=403, detail=f"AEGIS BLOCKED: {decision.reason}")
    
    # 2. Financial Consumption (if allowed)
    # Deduct small cost for API transaction
    wallet_manager.request_funds(0.5, trust_level, user_id=user_id)

    if decision.action == DecisionAction.DELAY and decision.delay_seconds:
        import asyncio
        await asyncio.sleep(decision.delay_seconds)

    return True

# --- Endpoints ---

@app.get("/status", dependencies=[Depends(verify_aegis)])
async def get_system_status():
    return {
        "core": "ONLINE",
        "aegis": "ACTIVE",
        "timestamp": datetime.now().isoformat(),
        "bridge": "PURPLE_TRIANGLE_V1"
    }

@app.get("/protocol", dependencies=[Depends(verify_aegis)])
async def read_protocol():
    try:
        protocol_path = os.path.join(os.path.dirname(__file__), '..', 'CORE', 'genesis_protocol.json')
        with open(protocol_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Genesis Protocol not found")

@app.post("/protocol")
async def update_protocol(update: GenesisProtocolUpdate, authorized: bool = Depends(verify_aegis)):
    try:
        # Convert Pydantic model to dict
        data = update.dict(exclude_unset=True)
        
        # Write to file
        protocol_path = os.path.join(os.path.dirname(__file__), '..', 'CORE', 'genesis_protocol.json')
        with open(protocol_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        return {"status": "success", "message": "Genesis Protocol updated securely."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory", dependencies=[Depends(verify_aegis)])
async def get_memory(q: Optional[str] = None, type: str = "all"):
    """Retrieve memory from the Soul."""
    if q:
        return soul_memory.recall(q, type)
    return soul_memory.get_full_memory()

@app.post("/memory")
async def save_memory(item: MemoryItem, authorized: bool = Depends(verify_aegis)):
    """Store new memory."""
    soul_memory.memorize(item.key, item.value, item.type)
    return {"status": "success", "message": "Memory stored in Soul Core."}

# --- CORE Endpoints ---

@app.get("/core/state")
async def get_core_state():
    """Live FSM State."""
    return core.get_status()

class CoreCommand(BaseModel):
    command: str

@app.post("/core/command", dependencies=[Depends(verify_aegis)])
async def trigger_core_command(cmd: CoreCommand):
    """Execute operational command."""
    core.execute_command(cmd.command)
    return {"status": "success", "new_state": core.state}

# --- Security Events Endpoint ---

@app.get("/core/security-events")
async def get_security_events(limit: int = 20):
    """
    Stream last N security events from AEGIS NDJSON log.
    Used by the UI to visualize security activity in real-time.
    """
    ndjson_path = event_tap.ndjson_path
    events = []
    try:
        if os.path.exists(ndjson_path):
            with open(ndjson_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # Take last N lines
            for line in lines[-limit:]:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        return {"events": [], "error": str(e)}
    
    # Count stats
    denied = sum(1 for e in events if e.get("status") == "denied")
    allowed = sum(1 for e in events if e.get("status") == "allowed")
    errors = sum(1 for e in events if e.get("status") == "error")
    
    return {
        "events": events,
        "stats": {
            "total": len(events),
            "denied": denied,
            "allowed": allowed,
            "errors": errors,
        }
    }

@app.get("/core/wallet-status")
async def get_wallet_status(request: Request):
    """Live Wallet metrics for a specific user."""
    user_id = request.headers.get("x-user-id", "anonymous")
    return wallet_manager.get_status(user_id=user_id)

if __name__ == "__main__":
    print(f"[PURPLE] Bridging Neural Link v3 (Security Events Active) on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)

