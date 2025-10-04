"""
Agent Context Management for Aether OS.

Provides dynamic context windows for agents based on role, phase, and task.
Ensures agents have appropriate situational awareness while managing context size.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging

from aether_os.orchestrator import ATOPhase

logger = logging.getLogger(__name__)


class ContextRefreshTrigger(Enum):
    """Triggers for context refresh."""
    PHASE_TRANSITION = "phase_transition"
    NEW_INTELLIGENCE = "new_intelligence"
    TASK_CHANGE = "task_change"
    PERIODIC = "periodic"
    MANUAL = "manual"


@dataclass
class DoctrineContext:
    """Doctrinal context for an agent."""
    relevant_procedures: List[Dict[str, Any]] = field(default_factory=list)
    applicable_policies: List[Dict[str, Any]] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)

    def size(self) -> int:
        """Estimate context size in tokens."""
        # Rough estimate: ~4 chars per token
        total_chars = 0
        for proc in self.relevant_procedures:
            total_chars += len(str(proc.get("content", "")))
        for policy in self.applicable_policies:
            total_chars += len(str(policy))
        for bp in self.best_practices:
            total_chars += len(bp)
        return total_chars // 4


@dataclass
class SituationalContext:
    """Current situational context for an agent."""
    current_threats: List[Dict[str, Any]] = field(default_factory=list)
    available_assets: List[Dict[str, Any]] = field(default_factory=list)
    active_missions: List[Dict[str, Any]] = field(default_factory=list)
    spectrum_status: Dict[str, Any] = field(default_factory=dict)

    def size(self) -> int:
        """Estimate context size in tokens."""
        total_chars = (
            len(str(self.current_threats)) +
            len(str(self.available_assets)) +
            len(str(self.active_missions)) +
            len(str(self.spectrum_status))
        )
        return total_chars // 4


@dataclass
class HistoricalContext:
    """Historical context from past cycles."""
    past_cycle_performance: List[Dict[str, Any]] = field(default_factory=list)
    recurring_issues: List[Dict[str, Any]] = field(default_factory=list)
    successful_patterns: List[Dict[str, Any]] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)

    def size(self) -> int:
        """Estimate context size in tokens."""
        total_chars = (
            len(str(self.past_cycle_performance)) +
            len(str(self.recurring_issues)) +
            len(str(self.successful_patterns)) +
            sum(len(lesson) for lesson in self.lessons_learned)
        )
        return total_chars // 4


@dataclass
class CollaborativeContext:
    """Context about other agents and shared state."""
    peer_agent_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pending_requests: List[Dict[str, Any]] = field(default_factory=list)
    shared_artifacts: List[Dict[str, Any]] = field(default_factory=list)

    def size(self) -> int:
        """Estimate context size in tokens."""
        total_chars = (
            len(str(self.peer_agent_states)) +
            len(str(self.pending_requests)) +
            len(str(self.shared_artifacts))
        )
        return total_chars // 4


@dataclass
class AgentContext:
    """
    Dynamic context window for an agent.

    Contains all information relevant to agent's current task,
    filtered and prioritized based on role and phase.
    """
    agent_id: str
    current_phase: ATOPhase
    current_task: Optional[str] = None

    # Core context components
    doctrinal_context: DoctrineContext = field(default_factory=DoctrineContext)
    situational_context: SituationalContext = field(default_factory=SituationalContext)
    historical_context: HistoricalContext = field(default_factory=HistoricalContext)
    collaborative_context: CollaborativeContext = field(default_factory=CollaborativeContext)

    # Context metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_refresh: datetime = field(default_factory=datetime.now)
    relevance_scores: Dict[str, float] = field(default_factory=dict)

    # Context tracking
    items_referenced: List[str] = field(default_factory=list)  # Track what agent actually uses

    def total_size(self) -> int:
        """Calculate total context size in tokens."""
        return (
            self.doctrinal_context.size() +
            self.situational_context.size() +
            self.historical_context.size() +
            self.collaborative_context.size()
        )

    def add_referenced_item(self, item_id: str):
        """Track that agent referenced a context item."""
        if item_id not in self.items_referenced:
            self.items_referenced.append(item_id)

    def get_utilization_rate(self) -> float:
        """Calculate what % of context was actually used."""
        total_items = (
            len(self.doctrinal_context.relevant_procedures) +
            len(self.situational_context.current_threats) +
            len(self.situational_context.available_assets) +
            len(self.historical_context.lessons_learned)
        )

        if total_items == 0:
            return 0.0

        return len(self.items_referenced) / total_items

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for passing to agents."""
        return {
            "agent_id": self.agent_id,
            "current_phase": self.current_phase.value if self.current_phase else None,
            "current_task": self.current_task,
            "doctrine": {
                "procedures": self.doctrinal_context.relevant_procedures,
                "policies": self.doctrinal_context.applicable_policies,
                "best_practices": self.doctrinal_context.best_practices,
            },
            "situation": {
                "threats": self.situational_context.current_threats,
                "assets": self.situational_context.available_assets,
                "missions": self.situational_context.active_missions,
                "spectrum": self.situational_context.spectrum_status,
            },
            "history": {
                "performance": self.historical_context.past_cycle_performance,
                "issues": self.historical_context.recurring_issues,
                "patterns": self.historical_context.successful_patterns,
                "lessons": self.historical_context.lessons_learned,
            },
            "collaboration": {
                "peer_states": self.collaborative_context.peer_agent_states,
                "pending_requests": self.collaborative_context.pending_requests,
                "shared_artifacts": self.collaborative_context.shared_artifacts,
            },
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "last_refresh": self.last_refresh.isoformat(),
                "total_size_tokens": self.total_size(),
            }
        }


@dataclass
class InformationItem:
    """An item of information that can be included in context."""
    item_id: str
    item_type: str  # "doctrine", "threat", "asset", etc.
    content: Any
    relevance_score: float = 0.0
    size_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
