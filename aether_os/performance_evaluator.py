"""
Agent Performance Evaluator for Aether OS.

Evaluates agent performance across multiple dimensions and generates reports.
"""

from typing import Dict, List, Optional, Any
from collections import defaultdict
import logging

from aether_os.performance_metrics import (
    AgentPerformanceMetrics,
    TaskExecutionMetric,
    CollaborationMetric,
    ResourceUsageMetric,
)
from aether_os.access_control import AGENT_PROFILES

logger = logging.getLogger(__name__)


class AgentPerformanceEvaluator:
    """
    Evaluates agent performance across multiple dimensions.

    Tracks:
    - Task execution metrics
    - Collaboration metrics
    - Resource usage
    - Process improvement contributions
    - Context utilization
    """

    def __init__(self, aether_os: Any):
        """
        Initialize performance evaluator.

        Args:
            aether_os: Reference to main AetherOS instance
        """
        self.aether_os = aether_os

        # Performance history
        self.performance_history: Dict[str, List[AgentPerformanceMetrics]] = defaultdict(list)

        # Metrics collection
        self.task_metrics: List[TaskExecutionMetric] = []
        self.collaboration_metrics: List[CollaborationMetric] = []
        self.resource_metrics: List[ResourceUsageMetric] = []

        # Baseline metrics (for comparison)
        self.baseline_metrics: Dict[str, AgentPerformanceMetrics] = {}

        logger.info("AgentPerformanceEvaluator initialized")

    def evaluate_agent_cycle_performance(
        self,
        agent_id: str,
        cycle_id: str,
    ) -> AgentPerformanceMetrics:
        """
        Evaluate agent's performance for a completed ATO cycle.

        Args:
            agent_id: Agent identifier
            cycle_id: ATO cycle ID

        Returns:
            Comprehensive performance metrics
        """
        logger.info(f"Evaluating {agent_id} performance for cycle {cycle_id}")

        metrics = AgentPerformanceMetrics(
            agent_id=agent_id,
            cycle_id=cycle_id,
        )

        # Mission Effectiveness
        metrics.mission_success_rate = self._calculate_mission_success(agent_id, cycle_id)
        metrics.output_quality_score = self._evaluate_output_quality(agent_id, cycle_id)
        metrics.doctrinal_compliance_rate = self._check_doctrinal_compliance(agent_id, cycle_id)

        # Efficiency
        metrics.avg_task_completion_time = self._calculate_avg_task_time(agent_id, cycle_id)
        metrics.timeline_adherence_rate = self._check_timeline_adherence(agent_id, cycle_id)
        metrics.resource_utilization = self._calculate_resource_utilization(agent_id, cycle_id)

        # Collaboration
        metrics.inter_agent_response_time = self._measure_response_time(agent_id, cycle_id)
        metrics.coordination_effectiveness = self._evaluate_coordination(agent_id, cycle_id)
        metrics.information_sharing_quality = self._evaluate_info_sharing(agent_id, cycle_id)

        # Process Improvement
        metrics.inefficiencies_identified = self._count_inefficiencies_flagged(agent_id, cycle_id)
        metrics.improvement_suggestions = self._count_improvement_suggestions(agent_id, cycle_id)
        metrics.suggestion_adoption_rate = self._calculate_adoption_rate(agent_id)

        # Learning & Adaptation
        metrics.lesson_learned_application = self._check_lesson_application(agent_id, cycle_id)
        metrics.performance_trend = self._analyze_trend(agent_id)
        metrics.context_utilization = self._measure_context_utilization(agent_id, cycle_id)

        # Robustness
        metrics.error_rate = self._calculate_error_rate(agent_id, cycle_id)
        metrics.recovery_success_rate = self._calculate_recovery_rate(agent_id, cycle_id)
        metrics.escalation_appropriateness = self._evaluate_escalations(agent_id, cycle_id)

        # Calculate overall score
        metrics.calculate_overall_score()

        # Store in history
        self.performance_history[agent_id].append(metrics)

        logger.info(
            f"Evaluation complete: {agent_id} overall score: {metrics.overall_score:.2f}"
        )

        return metrics

    def _calculate_mission_success(self, agent_id: str, cycle_id: str) -> float:
        """Calculate mission success rate."""
        agent_profile = AGENT_PROFILES.get(agent_id)
        if not agent_profile:
            return 0.0

        role = agent_profile.role

        # Get cycle outputs
        cycle = self.aether_os.orchestrator.current_cycle
        if not cycle or cycle.cycle_id != cycle_id:
            # Look in history
            for hist_cycle in self.aether_os.orchestrator.cycle_history:
                if hist_cycle.cycle_id == cycle_id:
                    cycle = hist_cycle
                    break

        if not cycle:
            return 0.0

        # Role-specific success calculation
        if role == "ew_planner":
            missions = cycle.outputs.get("ew_missions", [])
            if not missions:
                return 0.0
            # All missions planned successfully for prototype
            return 1.0

        elif role == "spectrum_manager":
            allocations = cycle.outputs.get("frequency_allocations", [])
            if not allocations:
                return 1.0  # No allocations needed is OK
            # Success if allocations exist
            return 1.0

        elif role == "ato_producer":
            ato_annex = cycle.outputs.get("ato_document")
            return 1.0 if ato_annex else 0.0

        elif role == "assessment":
            assessment = cycle.outputs.get("effectiveness_assessment")
            return 1.0 if assessment else 0.0

        else:
            # Default: check if agent produced expected outputs
            expected_outputs = {
                "ems_strategy": ["ems_strategy"],
                "ew_planner": ["ew_missions"],
                "spectrum_manager": ["frequency_allocations"],
                "ato_producer": ["ato_document"],
                "assessment": ["effectiveness_assessment", "lessons_learned"],
            }

            expected = expected_outputs.get(role, [])
            if not expected:
                return 1.0

            produced = sum(1 for output in expected if output in cycle.outputs)
            return produced / len(expected)

    def _evaluate_output_quality(self, agent_id: str, cycle_id: str) -> float:
        """Evaluate quality of agent outputs."""
        # Simplified quality evaluation
        # In production, would use LLM-based assessment

        cycle = self._get_cycle(cycle_id)
        if not cycle:
            return 0.0

        # Check if outputs exist and are non-empty
        agent_profile = AGENT_PROFILES.get(agent_id)
        if not agent_profile:
            return 0.0

        quality_scores = []

        # Basic quality: outputs exist and have content
        for output_name, output_data in cycle.outputs.items():
            if output_data and len(str(output_data)) > 0:
                quality_scores.append(1.0)
            else:
                quality_scores.append(0.0)

        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.5

    def _check_doctrinal_compliance(self, agent_id: str, cycle_id: str) -> float:
        """Check doctrinal compliance rate."""
        # In production, would check against doctrine KB
        # For prototype, assume high compliance
        return 0.95

    def _calculate_avg_task_time(self, agent_id: str, cycle_id: str) -> float:
        """Calculate average task completion time vs expected."""
        agent_tasks = [
            task for task in self.task_metrics
            if task.agent_id == agent_id and task.cycle_id == cycle_id
        ]

        if not agent_tasks:
            return 1.0  # Assume on-time

        time_ratios = [
            task.actual_time_hours / task.expected_time_hours
            for task in agent_tasks
            if task.expected_time_hours > 0
        ]

        return sum(time_ratios) / len(time_ratios) if time_ratios else 1.0

    def _check_timeline_adherence(self, agent_id: str, cycle_id: str) -> float:
        """Check timeline adherence."""
        agent_tasks = [
            task for task in self.task_metrics
            if task.agent_id == agent_id and task.cycle_id == cycle_id
        ]

        if not agent_tasks:
            return 1.0

        # Tasks completed within 130% of expected time are "on-time"
        on_time = sum(
            1 for task in agent_tasks
            if task.actual_time_hours <= task.expected_time_hours * 1.3
        )

        return on_time / len(agent_tasks)

    def _calculate_resource_utilization(self, agent_id: str, cycle_id: str) -> float:
        """Calculate resource utilization efficiency."""
        # Check if we have resource metrics
        agent_resources = [
            r for r in self.resource_metrics
            if r.agent_id == agent_id and r.cycle_id == cycle_id
        ]

        if not agent_resources:
            return 0.7  # Default moderate efficiency

        # For now, simple efficiency measure
        # In production, would track LLM usage, query efficiency, etc.
        return 0.8

    def _measure_response_time(self, agent_id: str, cycle_id: str) -> float:
        """Measure average inter-agent response time."""
        responses = [
            collab for collab in self.collaboration_metrics
            if collab.to_agent == agent_id and collab.response_time
        ]

        if not responses:
            return 5.0  # Assume 5 minutes average

        response_times = [
            (collab.response_time - collab.request_time).total_seconds() / 60
            for collab in responses
        ]

        return sum(response_times) / len(response_times)

    def _evaluate_coordination(self, agent_id: str, cycle_id: str) -> float:
        """Evaluate coordination effectiveness."""
        # Simplified: assume good coordination
        return 0.85

    def _evaluate_info_sharing(self, agent_id: str, cycle_id: str) -> float:
        """Evaluate information sharing quality."""
        # Check quality of responses provided to other agents
        responses = [
            collab for collab in self.collaboration_metrics
            if collab.from_agent == agent_id and collab.response_quality > 0
        ]

        if not responses:
            return 0.8  # Default

        avg_quality = sum(r.response_quality for r in responses) / len(responses)
        return avg_quality

    def _count_inefficiencies_flagged(self, agent_id: str, cycle_id: str) -> int:
        """Count process inefficiencies flagged by agent."""
        flags = self.aether_os.improvement_logger.get_flags_by_agent(agent_id)
        cycle_flags = [f for f in flags if f.ato_cycle_id == cycle_id]
        return len(cycle_flags)

    def _count_improvement_suggestions(self, agent_id: str, cycle_id: str) -> int:
        """Count improvement suggestions made."""
        # Count flags with suggestions
        flags = self.aether_os.improvement_logger.get_flags_by_agent(agent_id)
        cycle_flags = [
            f for f in flags
            if f.ato_cycle_id == cycle_id and f.suggested_improvement
        ]
        return len(cycle_flags)

    def _calculate_adoption_rate(self, agent_id: str) -> float:
        """Calculate improvement suggestion adoption rate."""
        # In production, would track which suggestions were implemented
        # For prototype, assume 50% adoption
        return 0.5

    def _check_lesson_application(self, agent_id: str, cycle_id: str) -> float:
        """Check if agent applied lessons learned."""
        # In production, would compare against past lessons
        return 0.7

    def _analyze_trend(self, agent_id: str) -> str:
        """Analyze performance trend over time."""
        history = self.performance_history.get(agent_id, [])

        if len(history) < 2:
            return "stable"

        # Compare last 2 cycles
        recent_scores = [m.overall_score for m in history[-2:]]

        if recent_scores[-1] > recent_scores[-2] + 0.05:
            return "improving"
        elif recent_scores[-1] < recent_scores[-2] - 0.05:
            return "degrading"
        else:
            return "stable"

    def _measure_context_utilization(self, agent_id: str, cycle_id: str) -> float:
        """Measure context utilization rate."""
        if not hasattr(self.aether_os, 'context_manager'):
            return 0.5  # No context manager

        stats = self.aether_os.context_manager.get_context_statistics(agent_id)

        if not stats:
            return 0.5

        return stats.get("avg_utilization_rate", 0.5)

    def _calculate_error_rate(self, agent_id: str, cycle_id: str) -> float:
        """Calculate error rate."""
        agent_tasks = [
            task for task in self.task_metrics
            if task.agent_id == agent_id and task.cycle_id == cycle_id
        ]

        if not agent_tasks:
            return 0.0

        errors = sum(1 for task in agent_tasks if not task.success)
        return errors / len(agent_tasks)

    def _calculate_recovery_rate(self, agent_id: str, cycle_id: str) -> float:
        """Calculate recovery success rate from errors."""
        # Simplified: assume good recovery
        return 0.9

    def _evaluate_escalations(self, agent_id: str, cycle_id: str) -> float:
        """Evaluate appropriateness of escalations."""
        # Simplified: assume appropriate escalations
        return 0.85

    def _get_cycle(self, cycle_id: str):
        """Get cycle by ID."""
        if self.aether_os.orchestrator.current_cycle and self.aether_os.orchestrator.current_cycle.cycle_id == cycle_id:
            return self.aether_os.orchestrator.current_cycle

        for cycle in self.aether_os.orchestrator.cycle_history:
            if cycle.cycle_id == cycle_id:
                return cycle

        return None

    def record_task_execution(
        self,
        agent_id: str,
        cycle_id: str,
        task_metric: TaskExecutionMetric,
    ):
        """Record task execution metric."""
        self.task_metrics.append(task_metric)

    def record_collaboration(self, collab_metric: CollaborationMetric):
        """Record collaboration metric."""
        self.collaboration_metrics.append(collab_metric)

    def record_resource_usage(self, resource_metric: ResourceUsageMetric):
        """Record resource usage metric."""
        self.resource_metrics.append(resource_metric)

    def generate_performance_report(
        self,
        agent_id: str,
        cycles: int = 5,
    ) -> str:
        """
        Generate comprehensive performance report.

        Args:
            agent_id: Agent to report on
            cycles: Number of recent cycles to include

        Returns:
            Formatted report string
        """
        history = self.performance_history.get(agent_id, [])

        if not history:
            return f"No performance data available for {agent_id}"

        recent = history[-cycles:]
        latest = recent[-1]

        report = f"""
================================================================
AGENT PERFORMANCE REPORT: {agent_id}
Period: Last {len(recent)} cycle(s)
================================================================

MISSION EFFECTIVENESS
---------------------
Success Rate: {latest.mission_success_rate:.1%}
Output Quality: {latest.output_quality_score:.2f}/1.0
Doctrinal Compliance: {latest.doctrinal_compliance_rate:.1%}

EFFICIENCY
----------
Avg Completion Time: {latest.avg_task_completion_time:.2f}x expected
Timeline Adherence: {latest.timeline_adherence_rate:.1%}
Resource Utilization: {latest.resource_utilization:.2f}/1.0

COLLABORATION
-------------
Response Time: {latest.inter_agent_response_time:.1f} minutes
Coordination Score: {latest.coordination_effectiveness:.2f}/1.0
Information Sharing: {latest.information_sharing_quality:.2f}/1.0

PROCESS IMPROVEMENT (Option C)
-------------------------------
Inefficiencies Flagged: {latest.inefficiencies_identified}
Improvement Suggestions: {latest.improvement_suggestions}
Adoption Rate: {latest.suggestion_adoption_rate:.1%}

LEARNING & ADAPTATION
---------------------
Lesson Application: {latest.lesson_learned_application:.1%}
Performance Trend: {latest.performance_trend}
Context Utilization: {latest.context_utilization:.1%}

ROBUSTNESS
----------
Error Rate: {latest.error_rate:.1%}
Recovery Success: {latest.recovery_success_rate:.1%}
Escalation Quality: {latest.escalation_appropriateness:.2f}/1.0

OVERALL SCORE: {latest.overall_score:.2f}/1.0

================================================================
"""

        return report

    def get_comparative_analysis(self) -> Dict[str, Any]:
        """Get comparative analysis across all agents."""
        analysis = {}

        for agent_id, history in self.performance_history.items():
            if not history:
                continue

            latest = history[-1]
            analysis[agent_id] = {
                "overall_score": latest.overall_score,
                "mission_success": latest.mission_success_rate,
                "efficiency": (2.0 - min(latest.avg_task_completion_time, 2.0)) / 2.0,
                "collaboration": latest.coordination_effectiveness,
                "process_improvement": latest.inefficiencies_identified,
                "trend": latest.performance_trend,
            }

        return analysis
