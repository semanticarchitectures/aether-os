"""
Performance Metrics for Aether OS Agents.

Defines comprehensive performance evaluation metrics across multiple dimensions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentPerformanceMetrics:
    """
    Comprehensive performance metrics for an agent.

    Covers 6 dimensions:
    1. Mission Effectiveness
    2. Efficiency
    3. Collaboration
    4. Process Improvement
    5. Learning & Adaptation
    6. Robustness
    """

    # Identification
    agent_id: str
    cycle_id: str
    evaluation_timestamp: datetime = field(default_factory=datetime.now)

    # 1. Mission Effectiveness
    mission_success_rate: float = 0.0  # 0.0-1.0
    output_quality_score: float = 0.0  # 0.0-1.0
    doctrinal_compliance_rate: float = 0.0  # 0.0-1.0

    # 2. Efficiency
    avg_task_completion_time: float = 1.0  # Ratio to expected time
    timeline_adherence_rate: float = 0.0  # 0.0-1.0
    resource_utilization: float = 0.0  # 0.0-1.0

    # 3. Collaboration
    inter_agent_response_time: float = 0.0  # Minutes
    coordination_effectiveness: float = 0.0  # 0.0-1.0
    information_sharing_quality: float = 0.0  # 0.0-1.0

    # 4. Process Improvement (Option C)
    inefficiencies_identified: int = 0
    improvement_suggestions: int = 0
    suggestion_adoption_rate: float = 0.0  # 0.0-1.0

    # 5. Learning & Adaptation
    lesson_learned_application: float = 0.0  # 0.0-1.0
    performance_trend: str = "stable"  # "improving", "stable", "degrading"
    context_utilization: float = 0.0  # 0.0-1.0

    # 6. Robustness
    error_rate: float = 0.0  # 0.0-1.0
    recovery_success_rate: float = 0.0  # 0.0-1.0
    escalation_appropriateness: float = 0.0  # 0.0-1.0

    # Overall score (weighted average)
    overall_score: float = 0.0  # 0.0-1.0

    def calculate_overall_score(self) -> float:
        """
        Calculate weighted overall score.

        Weights:
        - Mission Effectiveness: 30%
        - Efficiency: 20%
        - Collaboration: 15%
        - Process Improvement: 15%
        - Learning & Adaptation: 10%
        - Robustness: 10%
        """
        effectiveness = (
            self.mission_success_rate * 0.5 +
            self.output_quality_score * 0.3 +
            self.doctrinal_compliance_rate * 0.2
        )

        efficiency = (
            (2.0 - min(self.avg_task_completion_time, 2.0)) / 2.0 * 0.4 +
            self.timeline_adherence_rate * 0.3 +
            self.resource_utilization * 0.3
        )

        collaboration = (
            (1.0 / (1 + self.inter_agent_response_time / 30.0)) * 0.3 +
            self.coordination_effectiveness * 0.4 +
            self.information_sharing_quality * 0.3
        )

        improvement = (
            min(self.inefficiencies_identified / 5.0, 1.0) * 0.4 +
            min(self.improvement_suggestions / 3.0, 1.0) * 0.3 +
            self.suggestion_adoption_rate * 0.3
        )

        learning = (
            self.lesson_learned_application * 0.4 +
            {"improving": 1.0, "stable": 0.7, "degrading": 0.3}.get(self.performance_trend, 0.5) * 0.3 +
            self.context_utilization * 0.3
        )

        robustness = (
            (1.0 - self.error_rate) * 0.4 +
            self.recovery_success_rate * 0.3 +
            self.escalation_appropriateness * 0.3
        )

        self.overall_score = (
            effectiveness * 0.30 +
            efficiency * 0.20 +
            collaboration * 0.15 +
            improvement * 0.15 +
            learning * 0.10 +
            robustness * 0.10
        )

        return self.overall_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "agent_id": self.agent_id,
            "cycle_id": self.cycle_id,
            "evaluation_timestamp": self.evaluation_timestamp.isoformat(),
            "mission_effectiveness": {
                "success_rate": self.mission_success_rate,
                "output_quality": self.output_quality_score,
                "doctrinal_compliance": self.doctrinal_compliance_rate,
            },
            "efficiency": {
                "avg_task_time_ratio": self.avg_task_completion_time,
                "timeline_adherence": self.timeline_adherence_rate,
                "resource_utilization": self.resource_utilization,
            },
            "collaboration": {
                "response_time_minutes": self.inter_agent_response_time,
                "coordination_effectiveness": self.coordination_effectiveness,
                "information_sharing": self.information_sharing_quality,
            },
            "process_improvement": {
                "inefficiencies_identified": self.inefficiencies_identified,
                "improvement_suggestions": self.improvement_suggestions,
                "suggestion_adoption_rate": self.suggestion_adoption_rate,
            },
            "learning_adaptation": {
                "lesson_application": self.lesson_learned_application,
                "performance_trend": self.performance_trend,
                "context_utilization": self.context_utilization,
            },
            "robustness": {
                "error_rate": self.error_rate,
                "recovery_success_rate": self.recovery_success_rate,
                "escalation_appropriateness": self.escalation_appropriateness,
            },
            "overall_score": self.overall_score,
        }


@dataclass
class TaskExecutionMetric:
    """Metrics for a single task execution."""
    task_name: str
    agent_id: str
    cycle_id: str
    start_time: datetime
    end_time: datetime
    expected_time_hours: float
    actual_time_hours: float
    success: bool
    errors: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationMetric:
    """Metrics for inter-agent collaboration."""
    from_agent: str
    to_agent: str
    message_type: str
    request_time: datetime
    response_time: Optional[datetime] = None
    response_quality: float = 0.0  # Rated by requesting agent
    success: bool = True


@dataclass
class ResourceUsageMetric:
    """Metrics for resource usage."""
    agent_id: str
    cycle_id: str
    llm_calls: int = 0
    llm_tokens_used: int = 0
    database_queries: int = 0
    information_requests: int = 0
    context_size_tokens: int = 0
