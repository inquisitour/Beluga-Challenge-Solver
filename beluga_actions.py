from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class MoveJigBetweenRacks:
    """Move a jig from one rack to another rack."""
    jig_id: str
    from_rack_id: str
    to_rack_id: str

@dataclass(frozen=True)
class LoadJigToBeluga:
    """Load a jig from a rack to the Beluga."""
    jig_id: str
    from_rack_id: str

@dataclass(frozen=True)
class UnloadJigFromBeluga:
    """Unload a jig from the Beluga to a rack."""
    jig_id: str
    to_rack_id: str

@dataclass(frozen=True)
class SendJigToProduction:
    """Send a jig from a rack to production."""
    jig_id: str
    from_rack_id: str

@dataclass(frozen=True)
class ReturnEmptyJigFromFactory:
    """Return an empty jig from the factory to a rack."""
    jig_id: str
    to_rack_id: str

@dataclass(frozen=True)
class ProcessNextFlight:
    """Move to the next flight in the schedule."""
    pass