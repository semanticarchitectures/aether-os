"""
Process improvement subsystem for Aether OS.

Implements Option C: Agents follow doctrine exactly BUT maintain a process
improvement log to identify inefficiencies, contradictions, and automation opportunities.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class InefficencyType(Enum):
    """Types of process inefficiencies that can be flagged."""
    REDUNDANT_COORDINATION = "redundant_coordination"
    INFORMATION_GAP = "information_gap"
    TIMING_CONSTRAINT = "timing_constraint"
    DOCTRINE_CONTRADICTION = "doctrine_contradiction"
    AUTOMATION_OPPORTUNITY = "automation_opportunity"
    DECONFLICTION_ISSUE = "deconfliction_issue"
    RESOURCE_BOTTLENECK = "resource_bottleneck"


@dataclass
class ProcessImprovementFlag:
    """A single process improvement flag raised by an agent."""
    flag_id: str
    timestamp: datetime
    ato_cycle_id: str
    phase: str
    agent_id: str
    workflow_name: str
    inefficiency_type: InefficencyType
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    time_wasted_hours: Optional[float] = None
    suggested_improvement: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class ProcessImprovementPattern:
    """Identified pattern of recurring inefficiencies."""
    pattern_id: str
    inefficiency_type: InefficencyType
    occurrence_count: int
    affected_workflows: List[str]
    affected_phases: List[str]
    total_time_wasted_hours: float
    example_flags: List[ProcessImprovementFlag]
    recommendation: str
    priority: str  # low, medium, high


class ProcessImprovementLogger:
    """
    Tracks process inefficiencies and identifies patterns for improvement.

    This is the core implementation of Option C - agents follow doctrine
    but systematically identify where doctrine is inefficient.
    """

    def __init__(self):
        """Initialize the process improvement logger."""
        self.flags: List[ProcessImprovementFlag] = []
        self.patterns: List[ProcessImprovementPattern] = []
        self._flag_counter = 0
        self._pattern_counter = 0
        logger.info("ProcessImprovementLogger initialized")

    def flag_inefficiency(
        self,
        ato_cycle_id: str,
        phase: str,
        agent_id: str,
        workflow_name: str,
        inefficiency_type: InefficencyType,
        description: str,
        context: Optional[Dict[str, Any]] = None,
        time_wasted_hours: Optional[float] = None,
        suggested_improvement: Optional[str] = None,
        severity: str = "medium",
    ) -> ProcessImprovementFlag:
        """
        Flag a process inefficiency encountered during agent execution.

        Args:
            ato_cycle_id: ID of the current ATO cycle
            phase: Current ATO phase
            agent_id: ID of the agent raising the flag
            workflow_name: Name of the workflow/procedure being executed
            inefficiency_type: Type of inefficiency
            description: Detailed description of the inefficiency
            context: Additional context (optional)
            time_wasted_hours: Estimated time wasted (optional)
            suggested_improvement: Agent's suggested improvement (optional)
            severity: Severity level (low, medium, high, critical)

        Returns:
            The created ProcessImprovementFlag
        """
        self._flag_counter += 1
        flag = ProcessImprovementFlag(
            flag_id=f"FLAG-{self._flag_counter:06d}",
            timestamp=datetime.now(),
            ato_cycle_id=ato_cycle_id,
            phase=phase,
            agent_id=agent_id,
            workflow_name=workflow_name,
            inefficiency_type=inefficiency_type,
            description=description,
            context=context or {},
            time_wasted_hours=time_wasted_hours,
            suggested_improvement=suggested_improvement,
            severity=severity,
        )

        self.flags.append(flag)

        logger.warning(
            f"Process inefficiency flagged: {inefficiency_type.value} | "
            f"Agent: {agent_id} | Workflow: {workflow_name} | "
            f"Description: {description}"
        )

        return flag

    def analyze_patterns(
        self,
        ato_cycle_id: Optional[str] = None,
        min_occurrences: int = 3,
    ) -> List[ProcessImprovementPattern]:
        """
        Analyze flags to identify recurring patterns.

        Args:
            ato_cycle_id: Analyze only flags from specific ATO cycle (None for all)
            min_occurrences: Minimum occurrences to consider a pattern

        Returns:
            List of identified patterns
        """
        logger.info(f"Analyzing process improvement patterns (min_occurrences={min_occurrences})")

        # Filter flags
        flags_to_analyze = self.flags
        if ato_cycle_id:
            flags_to_analyze = [f for f in self.flags if f.ato_cycle_id == ato_cycle_id]

        # Group flags by workflow + inefficiency type
        grouped = defaultdict(list)
        for flag in flags_to_analyze:
            key = (flag.workflow_name, flag.inefficiency_type)
            grouped[key].append(flag)

        # Identify patterns
        patterns = []
        for (workflow, ineff_type), flag_list in grouped.items():
            if len(flag_list) >= min_occurrences:
                pattern = self._create_pattern(workflow, ineff_type, flag_list)
                patterns.append(pattern)

        self.patterns = patterns
        logger.info(f"Identified {len(patterns)} process improvement patterns")

        return patterns

    def _create_pattern(
        self,
        workflow: str,
        inefficiency_type: InefficencyType,
        flags: List[ProcessImprovementFlag],
    ) -> ProcessImprovementPattern:
        """Create a pattern from a group of related flags."""
        self._pattern_counter += 1

        # Calculate total time wasted
        total_time = sum(
            f.time_wasted_hours for f in flags if f.time_wasted_hours is not None
        )

        # Extract unique workflows and phases
        workflows = list(set(f.workflow_name for f in flags))
        phases = list(set(f.phase for f in flags))

        # Generate recommendation
        recommendation = self._generate_recommendation(
            workflow, inefficiency_type, flags
        )

        # Determine priority
        priority = self._determine_priority(len(flags), total_time)

        return ProcessImprovementPattern(
            pattern_id=f"PATTERN-{self._pattern_counter:04d}",
            inefficiency_type=inefficiency_type,
            occurrence_count=len(flags),
            affected_workflows=workflows,
            affected_phases=phases,
            total_time_wasted_hours=total_time,
            example_flags=flags[:3],  # Keep first 3 as examples
            recommendation=recommendation,
            priority=priority,
        )

    def _generate_recommendation(
        self,
        workflow: str,
        inefficiency_type: InefficencyType,
        flags: List[ProcessImprovementFlag],
    ) -> str:
        """Generate improvement recommendation based on pattern."""
        if inefficiency_type == InefficencyType.REDUNDANT_COORDINATION:
            return (
                f"Streamline coordination in '{workflow}': "
                f"Consolidate {len(flags)} redundant approval steps. "
                f"Consider implementing single approval authority or automated coordination."
            )
        elif inefficiency_type == InefficencyType.INFORMATION_GAP:
            return (
                f"Address information gap in '{workflow}': "
                f"Grant direct access to required data sources or pre-populate "
                f"information at workflow start. Occurred {len(flags)} times."
            )
        elif inefficiency_type == InefficencyType.TIMING_CONSTRAINT:
            return (
                f"Adjust timeline for '{workflow}': "
                f"Current doctrine timeline is unrealistic. Observed {len(flags)} instances "
                f"where execution exceeded expected time by >30%."
            )
        elif inefficiency_type == InefficencyType.DOCTRINE_CONTRADICTION:
            return (
                f"Resolve doctrine contradiction in '{workflow}': "
                f"Conflicting guidance detected {len(flags)} times. "
                f"Requires doctrine update or clarification."
            )
        elif inefficiency_type == InefficencyType.AUTOMATION_OPPORTUNITY:
            return (
                f"Automate '{workflow}': "
                f"Manual process repeated {len(flags)} times with consistent inputs. "
                f"High automation potential."
            )
        elif inefficiency_type == InefficencyType.DECONFLICTION_ISSUE:
            return (
                f"Improve spectrum deconfliction in '{workflow}': "
                f"Recurring conflicts ({len(flags)} instances). "
                f"Consider pre-allocation or enhanced coordination tools."
            )
        elif inefficiency_type == InefficencyType.RESOURCE_BOTTLENECK:
            return (
                f"Address resource bottleneck in '{workflow}': "
                f"Insufficient assets/time detected {len(flags)} times. "
                f"Requires resource reallocation or timeline adjustment."
            )
        else:
            return f"Review '{workflow}' for process improvement opportunities."

    def _determine_priority(self, occurrence_count: int, time_wasted: float) -> str:
        """Determine priority based on occurrences and time wasted."""
        if occurrence_count >= 10 or time_wasted >= 10:
            return "high"
        elif occurrence_count >= 5 or time_wasted >= 5:
            return "medium"
        else:
            return "low"

    def get_flags_by_cycle(self, ato_cycle_id: str) -> List[ProcessImprovementFlag]:
        """Get all flags for a specific ATO cycle."""
        return [f for f in self.flags if f.ato_cycle_id == ato_cycle_id]

    def get_flags_by_agent(self, agent_id: str) -> List[ProcessImprovementFlag]:
        """Get all flags raised by a specific agent."""
        return [f for f in self.flags if f.agent_id == agent_id]

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of process improvement flags."""
        total_flags = len(self.flags)

        # Count by type
        by_type = defaultdict(int)
        for flag in self.flags:
            by_type[flag.inefficiency_type.value] += 1

        # Count by agent
        by_agent = defaultdict(int)
        for flag in self.flags:
            by_agent[flag.agent_id] += 1

        # Total time wasted
        total_time_wasted = sum(
            f.time_wasted_hours for f in self.flags if f.time_wasted_hours is not None
        )

        return {
            "total_flags": total_flags,
            "by_type": dict(by_type),
            "by_agent": dict(by_agent),
            "total_time_wasted_hours": total_time_wasted,
            "patterns_identified": len(self.patterns),
        }

    def generate_report(self) -> str:
        """Generate a human-readable process improvement report."""
        stats = self.get_summary_statistics()

        report = "=" * 60 + "\n"
        report += "PROCESS IMPROVEMENT REPORT\n"
        report += "=" * 60 + "\n\n"

        report += f"Total Flags Raised: {stats['total_flags']}\n"
        report += f"Total Time Wasted: {stats['total_time_wasted_hours']:.1f} hours\n"
        report += f"Patterns Identified: {stats['patterns_identified']}\n\n"

        report += "Flags by Type:\n"
        for ineff_type, count in stats['by_type'].items():
            report += f"  - {ineff_type}: {count}\n"

        report += "\nFlags by Agent:\n"
        for agent, count in stats['by_agent'].items():
            report += f"  - {agent}: {count}\n"

        if self.patterns:
            report += "\n" + "=" * 60 + "\n"
            report += "IDENTIFIED PATTERNS\n"
            report += "=" * 60 + "\n\n"

            # Sort patterns by priority
            sorted_patterns = sorted(
                self.patterns,
                key=lambda p: (
                    {"high": 0, "medium": 1, "low": 2}[p.priority],
                    -p.occurrence_count
                ),
            )

            for pattern in sorted_patterns:
                report += f"Pattern {pattern.pattern_id} [{pattern.priority.upper()} PRIORITY]\n"
                report += f"  Type: {pattern.inefficiency_type.value}\n"
                report += f"  Occurrences: {pattern.occurrence_count}\n"
                report += f"  Time Wasted: {pattern.total_time_wasted_hours:.1f} hours\n"
                report += f"  Affected Workflows: {', '.join(pattern.affected_workflows)}\n"
                report += f"  Recommendation: {pattern.recommendation}\n\n"

        return report
