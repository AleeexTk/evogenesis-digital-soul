import sys
import os

# Добавляем корневую директорию в путь импорта, чтобы AEGIS мог видеть свои модули
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from PROVOCATEUR.AEGIS.core.event_tap import EventTap
from PROVOCATEUR.AEGIS.core.policy_engine import PolicyEngine

def test_aegis():
    print("[PROVOCATEUR] Инициализация AEGIS Test Suite...")
    
    # Init
    tap = EventTap(ndjson_path="c:\\Project_Pyramid2024\\PROVOCATEUR\\AEGIS\\security.ndjson")
    engine = PolicyEngine(config_path="c:\\Project_Pyramid2024\\PROVOCATEUR\\AEGIS\\security_policies.yaml")
    
    print("[PROVOCATEUR] AEGIS Core Online.")
    
    # Test Cases
    scenarios = [
        {"user_id": "admin", "trust_level": 1.0, "origin": "http", "intent": "read", "method": "GET"},
        {"user_id": "unknown_actor", "trust_level": 0.0, "origin": "http", "intent": "write", "method": "POST"},
        {"user_id": "suspicious_user", "trust_level": 0.2, "origin": "llm", "intent": "chat"},
    ]
    
    for ctx in scenarios:
        print(f"\n--- Testing Context: {ctx['user_id']} ---")
        decision = engine.evaluate(ctx)
        print(f"Decision: {decision.action.upper()} | Reason: {decision.reason}")
        
        # Log result
        tap.log_simple(
            origin=ctx.get("origin"),
            intent=ctx.get("intent"),
            status=decision.action.value,
            details=f"Reason: {decision.reason}"
        )

    print("\n[PROVOCATEUR] Тесты завершены. Проверьте security.ndjson.")

if __name__ == "__main__":
    test_aegis()
