from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Standing(str, Enum):
    UNKNOWN = "UNKNOWN"
    PARTIAL_ALIVE = "PARTIAL_ALIVE"
    ALIVE = "ALIVE"
    BLOCKED = "BLOCKED"
    BUILD_BROKEN = "BUILD_BROKEN"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class Refusal:
    code: str
    object_id: str
    law: str
    observed: Any
    expected: Any
    repair: str

    @property
    def state(self) -> str:
        return f"REFUSED:{self.code}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "code": self.code,
            "object": self.object_id,
            "law": self.law,
            "observed": self.observed,
            "expected": self.expected,
            "repair": self.repair,
        }


class TCPSRefused(RuntimeError):
    def __init__(self, refusal: Refusal):
        super().__init__(refusal.state)
        self.refusal = refusal
