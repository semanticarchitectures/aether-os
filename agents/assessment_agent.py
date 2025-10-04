"""
Assessment Agent for Aether OS.

Assesses ATO cycle effectiveness and generates lessons learned during
Phase 6 (Assessment). Also analyzes process improvement flags.
"""

from typing import Dict, Any, List
import logging

from agents.base_agent import BaseAetherAgent
from aether_os.access_control import InformationCategory

logger = logging.getLogger(__name__)


class AssessmentAgent(BaseAetherAgent):
    """
    Assessment Agent.

    Active Phases: Phase 6 (Assessment)
    Role: Assesses effectiveness and generates lessons learned
    Access Level: OPERATIONAL
    """

    def __init__(self, aether_os: Any):
        """Initialize Assessment Agent."""
        super().__init__(agent_id="assessment_agent", aether_os=aether_os)

    async def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """Execute tasks for the current phase."""
        if phase == "PHASE6_ASSESSMENT":
            return await self._execute_phase6(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase: {phase}")
            return {}

    async def _execute_phase6(self, cycle_id: str) -> Dict[str, Any]:
        """
        Execute Phase 6 (Assessment) tasks.

        Assess ATO cycle and generate lessons learned.
        """
        logger.info(f"[{self.agent_id}] Executing Phase 6 (Assessment) for cycle {cycle_id}")

        outputs = {}

        # Assess ATO cycle
        assessment = self.execute_doctrinal_procedure(
            procedure_name="Assess ATO Cycle",
            procedure_fn=self.assess_ato_cycle,
            expected_time_hours=8.0,
            cycle_id=cycle_id,
            phase="PHASE6_ASSESSMENT",
        )

        outputs["effectiveness_assessment"] = assessment

        # Analyze process improvements (Option C feature)
        process_analysis = self.execute_doctrinal_procedure(
            procedure_name="Analyze Doctrine Effectiveness",
            procedure_fn=self._analyze_doctrine_effectiveness,
            expected_time_hours=4.0,
            cycle_id=cycle_id,
            phase="PHASE6_ASSESSMENT",
        )

        outputs["process_improvement_analysis"] = process_analysis

        # Generate lessons learned
        lessons_learned = self._generate_lessons_learned(assessment, process_analysis)
        outputs["lessons_learned"] = lessons_learned

        # Record outputs
        self.aether_os.orchestrator.record_output("effectiveness_assessment", assessment)
        self.aether_os.orchestrator.record_output("lessons_learned", lessons_learned)

        return outputs

    def assess_ato_cycle(self, cycle_id: str) -> Dict[str, Any]:
        """
        Assess ATO cycle effectiveness.

        Evaluates mission success, timeline adherence, and process execution.
        """
        logger.info(f"[{self.agent_id}] Assessing ATO cycle {cycle_id}")

        # Get cycle data
        current_cycle = self.aether_os.orchestrator.current_cycle
        if not current_cycle:
            logger.error("No current cycle to assess")
            return {}

        # Collect execution data (would come from Phase 5 in production)
        execution_data = current_cycle.outputs.get("execution_data", {})

        # Assess mission effectiveness
        mission_assessment = self._assess_mission_effectiveness(current_cycle)

        # Assess timeline adherence
        timeline_assessment = self._assess_timeline_adherence(current_cycle)

        # Assess coordination effectiveness
        coordination_assessment = self._assess_coordination_effectiveness(current_cycle)

        assessment = {
            "cycle_id": cycle_id,
            "mission_effectiveness": mission_assessment,
            "timeline_adherence": timeline_assessment,
            "coordination_effectiveness": coordination_assessment,
            "overall_rating": self._calculate_overall_rating(
                mission_assessment,
                timeline_assessment,
                coordination_assessment,
            ),
        }

        logger.info(
            f"[{self.agent_id}] Assessment complete - "
            f"Overall rating: {assessment['overall_rating']}"
        )

        return assessment

    def _assess_mission_effectiveness(self, cycle: Any) -> Dict[str, Any]:
        """Assess effectiveness of EMS missions."""
        ew_missions = cycle.outputs.get("ew_missions", [])

        # In production, would analyze actual execution data
        # For prototype, simulated assessment

        successful_missions = len([m for m in ew_missions if m.get("status") != "failed"])
        total_missions = len(ew_missions)

        success_rate = successful_missions / total_missions if total_missions > 0 else 0

        return {
            "total_missions": total_missions,
            "successful_missions": successful_missions,
            "success_rate": success_rate,
            "rating": "effective" if success_rate >= 0.8 else "needs_improvement",
        }

    def _assess_timeline_adherence(self, cycle: Any) -> Dict[str, Any]:
        """Assess adherence to ATO cycle timeline."""
        phase_history = cycle.phase_history

        # Check if all phases completed on time
        # In production, would compare actual vs planned phase transitions

        return {
            "phases_completed": len(phase_history),
            "on_time": True,  # Simplified for prototype
            "delays": [],
            "rating": "on_time",
        }

    def _assess_coordination_effectiveness(self, cycle: Any) -> Dict[str, Any]:
        """Assess effectiveness of inter-agent coordination."""
        # In production, would analyze message passing, response times, etc.

        return {
            "coordination_issues": 0,
            "response_time_avg_minutes": 5.0,
            "rating": "effective",
        }

    def _calculate_overall_rating(
        self,
        mission: Dict,
        timeline: Dict,
        coordination: Dict,
    ) -> str:
        """Calculate overall cycle rating."""
        # Simple rating logic
        if (
            mission.get("rating") == "effective"
            and timeline.get("rating") == "on_time"
            and coordination.get("rating") == "effective"
        ):
            return "highly_effective"
        elif mission.get("success_rate", 0) >= 0.6:
            return "effective"
        else:
            return "needs_improvement"

    def _analyze_doctrine_effectiveness(self, cycle_id: str) -> Dict[str, Any]:
        """
        Analyze doctrine effectiveness (Option C feature).

        Reviews process improvement flags to identify systemic issues.
        """
        logger.info(f"[{self.agent_id}] Analyzing doctrine effectiveness...")

        # Get process improvement flags for this cycle
        flags = self.aether_os.improvement_logger.get_flags_by_cycle(cycle_id)

        logger.info(f"Found {len(flags)} process improvement flags for cycle {cycle_id}")

        # Analyze patterns across all cycles
        patterns = self.aether_os.improvement_logger.analyze_patterns(
            ato_cycle_id=None,  # Analyze across all cycles
            min_occurrences=2,  # Lower threshold for prototype
        )

        # Categorize findings
        critical_issues = [p for p in patterns if p.priority == "high"]
        moderate_issues = [p for p in patterns if p.priority == "medium"]

        analysis = {
            "cycle_id": cycle_id,
            "flags_this_cycle": len(flags),
            "patterns_identified": len(patterns),
            "critical_issues": len(critical_issues),
            "moderate_issues": len(moderate_issues),
            "critical_issue_details": [
                {
                    "pattern_id": p.pattern_id,
                    "type": p.inefficiency_type.value,
                    "occurrences": p.occurrence_count,
                    "recommendation": p.recommendation,
                }
                for p in critical_issues
            ],
            "time_wasted_hours": sum(
                p.total_time_wasted_hours for p in patterns
            ),
        }

        logger.info(
            f"[{self.agent_id}] Doctrine analysis: "
            f"{len(critical_issues)} critical issues, "
            f"{len(moderate_issues)} moderate issues"
        )

        return analysis

    def _generate_lessons_learned(
        self,
        assessment: Dict[str, Any],
        process_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate lessons learned report.

        Combines operational assessment with process improvement insights.
        """
        logger.info(f"[{self.agent_id}] Generating lessons learned...")

        lessons = {
            "cycle_id": assessment.get("cycle_id"),
            "overall_performance": assessment.get("overall_rating"),
            "key_findings": [],
            "recommendations": [],
            "process_improvements": [],
        }

        # Add findings based on assessment
        if assessment.get("mission_effectiveness", {}).get("success_rate", 1.0) < 0.8:
            lessons["key_findings"].append(
                "Mission success rate below 80% - requires investigation"
            )
            lessons["recommendations"].append(
                "Review mission planning procedures and asset allocation"
            )

        # Add process improvement insights (Option C)
        if process_analysis.get("critical_issues", 0) > 0:
            lessons["key_findings"].append(
                f"Identified {process_analysis['critical_issues']} critical process inefficiencies"
            )

            for issue in process_analysis.get("critical_issue_details", []):
                lessons["process_improvements"].append({
                    "issue_type": issue["type"],
                    "occurrences": issue["occurrences"],
                    "recommendation": issue["recommendation"],
                    "priority": "high",
                })

        # Add general recommendations
        lessons["recommendations"].append(
            "Continue monitoring process improvement flags for emerging patterns"
        )

        logger.info(
            f"[{self.agent_id}] Generated {len(lessons['key_findings'])} findings "
            f"and {len(lessons['recommendations'])} recommendations"
        )

        return lessons

    def get_process_improvement_report(self) -> str:
        """Get formatted process improvement report."""
        return self.aether_os.improvement_logger.generate_report()
