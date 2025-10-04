"""
Aether OS: AI-mediated operating system layer for USAF EMS Operations.

This package provides the core framework for orchestrating AI agents in support
of Air Operations Center (AOC) Electromagnetic Spectrum operations.
"""

from aether_os.core import AetherOS
from aether_os.access_control import AccessLevel, InformationCategory, AgentAccessProfile
from aether_os.orchestrator import ATOPhase, ATOCycleOrchestrator

__version__ = "0.1.0"
__all__ = [
    "AetherOS",
    "AccessLevel",
    "InformationCategory",
    "AgentAccessProfile",
    "ATOPhase",
    "ATOCycleOrchestrator",
]
