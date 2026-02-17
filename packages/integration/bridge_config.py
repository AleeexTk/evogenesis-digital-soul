"""Configuration model for cross-repo service integration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BridgeConfig:
    """Runtime settings for linking digital-soul with EvoGenesis and EvoPyramid services."""

    digital_soul_api_base: str = "http://127.0.0.1:8080"
    evogenesis_api_base: str = "http://127.0.0.1:8090"
    evopyramid_api_base: str = "http://127.0.0.1:5173"
    auth_token: str = ""

    @classmethod
    def from_env(cls) -> "BridgeConfig":
        return cls(
            digital_soul_api_base=os.getenv("DIGITAL_SOUL_API_BASE", "http://127.0.0.1:8080"),
            evogenesis_api_base=os.getenv("EVOGENESIS_API_BASE", "http://127.0.0.1:8090"),
            evopyramid_api_base=os.getenv("EVOPYRAMID_API_BASE", "http://127.0.0.1:5173"),
            auth_token=os.getenv("EVO_BRIDGE_AUTH_TOKEN", ""),
        )

    def validate(self) -> None:
        for name, value in (
            ("digital_soul_api_base", self.digital_soul_api_base),
            ("evogenesis_api_base", self.evogenesis_api_base),
            ("evopyramid_api_base", self.evopyramid_api_base),
        ):
            if not (value.startswith("http://") or value.startswith("https://")):
                raise ValueError(f"{name} must start with http:// or https://")
