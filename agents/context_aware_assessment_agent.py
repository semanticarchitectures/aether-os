"""
Context-Aware Assessment Agent for Aether OS.

Assesses ATO cycle effectiveness and generates lessons learned with
LLM-powered analysis grounded in mission data and process metrics.
"""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from aether_os.context_aware_agent import ContextAwareBaseAgent
from aether_os.llm_client import LLMProvider
from aether_os.orchestrator import ATOPhase
from aether_os.prompt_builder import get_task_template

logger = logging.getLogger(__name__)


class MissionEffectiveness(BaseModel):
    """Mission effectiveness assessment."""
    total_missions: int
    successful_missions: int
    failed_missions: int
    success_rate: float = Field(ge=0.0, le=1.0)
    effectiveness_rating: str  # effective, needs_improvement, ineffective
    key_successes: List[str]
    key_failures: List[str]


class ProcessEfficiency(BaseModel):
    """Process efficiency assessment."""
    total_flags: int
    critical_issues: int
    moderate_issues: int
    minor_issues: int
    time_wasted_hours: float
    top_inefficiencies: List[str]
    efficiency_rating: str  # efficient, acceptable, inefficient


class LessonLearned(BaseModel):
    """Individual lesson learned."""
    lesson_id: str
    category: str  # tactical, operational, process, coordination
    description: str
    recommendation: str
    priority: str  # high, medium, low
    apply_to: List[str] = Field(description="Which agents/processes to apply to")


class AssessmentResponse(BaseModel):
    """Structured response for cycle assessment."""
    cycle_id: str
    overall_rating: str  # highly_effective, effective, needs_improvement, ineffective
    mission_effectiveness: MissionEffectiveness
    process_efficiency: ProcessEfficiency
    lessons_learned: List[LessonLearned] = Field(description="Lessons learned")
    recommendations: List[str] = Field(description="Strategic recommendations")
    doctrine_assessment: str = Field(description="Assessment of doctrine effectiveness")
    context_citations: List[str] = Field(description="Context element IDs used")
    doctrine_citations: List[str] = Field(description="Specific doctrine references")
    confidence: float = Field(ge=0.0, le=1.0)


class ContextAwareAssessmentAgent(ContextAwareBaseAgent):
    """
    Context-aware Assessment Agent.

    Active during Phase 6 (Assessment).
    Assesses ATO cycle effectiveness and generates lessons learned using
    LLM reasoning grounded in execution data, process metrics, and doctrine.
    """

    def __init__(self, aether_os: Any):
        """Initialize context-aware Assessment Agent."""
        super().__init__(
            agent_id="assessment_agent",
            aether_os=aether_os,
            role="assessment",
            llm_provider=LLMProvider.ANTHROPIC,
            max_context_tokens=16000,  # Large context for comprehensive assessment
            use_semantic_tracking=True,
        )

        logger.info(f"[{self.agent_id}] Context-aware Assessment Agent initialized")

    async def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """
        Execute phase-specific tasks.

        Args:
            phase: Current ATO phase
            cycle_id: ATO cycle identifier

        Returns:
            Task execution results
        """
        logger.info(f"[{self.agent_id}] Executing tasks for {phase}, cycle {cycle_id}")

        if phase == "PHASE6_ASSESSMENT":
            return await self._assess_cycle(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase {phase}")
            return {"success": False, "reason": f"Not active in {phase}"}

    async def _assess_cycle(self, cycle_id: str) -> Dict[str, Any]:
        """
        Assess ATO cycle during Phase 6.

        Evaluates mission effectiveness, process efficiency, and generates
        lessons learned with process improvement recommendations.
        """
        logger.info(f"[{self.agent_id}] Assessing ATO cycle")

        task = """Assess the ATO cycle effectiveness:

1. Mission Effectiveness Analysis
   - Review all EMS missions executed (from context)
   - Analyze success/failure rates
   - Identify key successes and failures
   - Rate overall mission effectiveness

2. Process Efficiency Analysis
   - Review process improvement flags (from context)
   - Identify recurring inefficiencies
   - Calculate time wasted due to process issues
   - Rate process efficiency

3. Lessons Learned Generation
   - Extract tactical lessons (mission execution)
   - Extract operational lessons (coordination, timing)
   - Extract process lessons (workflow improvements)
   - Prioritize lessons by impact

4. Doctrine Effectiveness Assessment (Option C)
   - Evaluate if doctrine procedures worked as expected
   - Identify doctrine gaps or contradictions
   - Recommend doctrine updates if needed

5. Strategic Recommendations
   - Recommend improvements for next cycle
   - Identify automation opportunities
   - Suggest resource adjustments

Provide comprehensive assessment with data-driven insights."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=AssessmentResponse,
            temperature=0.4,  # Higher temp for analytical insights
            max_tokens=6000,
        )

        if response["success"]:
            logger.info(
                f"[{self.agent_id}] Assessment complete: "
                f"{response.get('context_utilization', 0):.1%} context utilization"
            )

            # Store assessment
            self.artifacts["cycle_assessment"] = response.get("content")
            self.artifacts["assessment_cycle_id"] = cycle_id

        return response

    def assess_mission_effectiveness(
        self,
        missions: List[Dict[str, Any]],
        execution_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assess effectiveness of executed missions.

        Args:
            missions: List of missions executed
            execution_data: Execution results and metrics

        Returns:
            Mission effectiveness assessment
        """
        missions_str = "\n".join([
            f"- {m.get('mission_id')}: {m.get('mission_type')}, status: {m.get('status', 'unknown')}, target: {m.get('target_id')}"
            for m in missions
        ])

        execution_str = ""
        if execution_data:
            execution_str = f"\n\nEXECUTION DATA:\n{execution_data}"

        task = f"""Assess mission effectiveness:

MISSIONS EXECUTED:
{missions_str}
{execution_str}

Assessment requirements:
1. Calculate success rate
2. Identify missions that achieved objectives
3. Identify missions that failed or partially succeeded
4. Analyze root causes of failures
5. Identify best practices from successes
6. Rate overall effectiveness (effective/needs_improvement/ineffective)
7. Cite relevant performance doctrine

Provide detailed effectiveness assessment."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=AssessmentResponse,
            temperature=0.3,
            max_tokens=4000,
        )

        return response

    def analyze_process_efficiency(
        self,
        cycle_id: str,
    ) -> Dict[str, Any]:
        """
        Analyze process efficiency from improvement flags (Option C).

        Args:
            cycle_id: ATO cycle to analyze

        Returns:
            Process efficiency analysis
        """
        task = f"""Analyze process efficiency for cycle {cycle_id}:

Review process improvement flags from context:
1. Categorize by severity (critical/moderate/minor)
2. Identify recurring patterns
3. Calculate total time wasted
4. Prioritize issues by impact
5. Generate specific recommendations for each issue type

For each critical issue:
- Describe the inefficiency
- Quantify the impact
- Recommend specific fix (automation, process change, access grant, etc.)
- Cite relevant doctrine if process change needed

Focus on actionable, data-driven recommendations."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=AssessmentResponse,
            temperature=0.35,
            max_tokens=5000,
        )

        return response

    def generate_lessons_learned(
        self,
        cycle_id: str,
        mission_assessment: Optional[Dict[str, Any]] = None,
        process_assessment: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate lessons learned report.

        Args:
            cycle_id: ATO cycle ID
            mission_assessment: Mission effectiveness data
            process_assessment: Process efficiency data

        Returns:
            Lessons learned with recommendations
        """
        assessment_context = ""
        if mission_assessment:
            assessment_context += f"\n\nMISSION ASSESSMENT:\n{mission_assessment}"
        if process_assessment:
            assessment_context += f"\n\nPROCESS ASSESSMENT:\n{process_assessment}"

        task = f"""Generate lessons learned report for cycle {cycle_id}:
{assessment_context}

Lessons learned requirements:
1. Tactical Lessons
   - Mission execution techniques that worked well
   - Asset employment lessons
   - Threat response lessons

2. Operational Lessons
   - Coordination improvements
   - Timing optimization
   - Resource allocation insights

3. Process Lessons (Option C)
   - Workflow inefficiencies identified
   - Automation opportunities
   - Doctrine gaps or contradictions

4. Strategic Recommendations
   - Long-term improvements
   - Capability gaps
   - Training needs

For each lesson:
- Provide specific, actionable description
- Recommend concrete action
- Prioritize by impact (high/medium/low)
- Identify which agents/processes should implement

Generate comprehensive lessons learned."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=AssessmentResponse,
            temperature=0.4,
            max_tokens=5000,
        )

        return response

    def assess_doctrine_effectiveness(
        self,
        cycle_id: str,
    ) -> Dict[str, Any]:
        """
        Assess doctrine effectiveness (Option C feature).

        Args:
            cycle_id: ATO cycle to assess

        Returns:
            Doctrine effectiveness assessment
        """
        task = f"""Assess doctrine effectiveness for cycle {cycle_id}:

Based on process improvement flags and mission outcomes (from context):

1. Did doctrine procedures work as expected?
   - Which procedures executed smoothly
   - Which procedures caused delays or issues
   - Where doctrine was unclear or contradictory

2. Identify doctrine gaps:
   - Scenarios not covered by current doctrine
   - Emerging threats requiring new procedures
   - Technology capabilities not addressed

3. Recommend doctrine updates:
   - Specific procedure changes
   - New procedures needed
   - Doctrine sections to clarify

4. Process improvement opportunities:
   - Where doctrine could be streamlined
   - Where automation could assist
   - Where approval processes are excessive

NOTE: This is Option C - agents follow doctrine but flag issues.
Focus on constructive recommendations to improve doctrine effectiveness.

Provide detailed doctrine assessment."""

        response = self.generate_with_context(
            task_description=task,
            temperature=0.35,
            max_tokens=4000,
        )

        return response

    def compare_cycles(
        self,
        cycle_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Compare multiple ATO cycles to identify trends.

        Args:
            cycle_ids: List of cycle IDs to compare

        Returns:
            Comparative analysis
        """
        task = f"""Compare ATO cycles {', '.join(cycle_ids)}:

Cross-cycle analysis:
1. Performance trends
   - Is mission success rate improving?
   - Are process inefficiencies decreasing?
   - Are coordination issues being resolved?

2. Recurring issues
   - Issues appearing in multiple cycles
   - Systemic vs one-time problems

3. Improvement trajectory
   - Lessons learned being applied?
   - Recommended fixes being implemented?

4. Emerging patterns
   - New threat types
   - New coordination challenges
   - New capability gaps

Provide trend analysis with strategic insights."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=AssessmentResponse,
            temperature=0.4,
            max_tokens=5000,
        )

        return response

    def handle_message(self, sender: str, message_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle messages from other agents or systems.

        Args:
            sender: Message sender ID
            message_type: Type of message
            payload: Message payload

        Returns:
            Response dictionary
        """
        logger.info(f"[{self.agent_id}] Received {message_type} from {sender}")

        if message_type == "assess_cycle":
            cycle_id = payload.get("cycle_id", "unknown")
            # Trigger full assessment
            import asyncio
            return asyncio.run(self._assess_cycle(cycle_id))

        elif message_type == "assess_missions":
            return self.assess_mission_effectiveness(
                missions=payload.get("missions", []),
                execution_data=payload.get("execution_data"),
            )

        elif message_type == "analyze_process":
            return self.analyze_process_efficiency(
                cycle_id=payload.get("cycle_id", "unknown"),
            )

        elif message_type == "generate_lessons":
            return self.generate_lessons_learned(
                cycle_id=payload.get("cycle_id", "unknown"),
                mission_assessment=payload.get("mission_assessment"),
                process_assessment=payload.get("process_assessment"),
            )

        elif message_type == "assess_doctrine":
            return self.assess_doctrine_effectiveness(
                cycle_id=payload.get("cycle_id", "unknown"),
            )

        elif message_type == "compare_cycles":
            return self.compare_cycles(
                cycle_ids=payload.get("cycle_ids", []),
            )

        else:
            # Use context-aware message processing
            return self.process_message_with_context(message_type, payload)
