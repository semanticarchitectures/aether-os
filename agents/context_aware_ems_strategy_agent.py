"""
Context-Aware EMS Strategy Agent for Aether OS.

Develops electromagnetic spectrum strategy with LLM-powered reasoning
grounded in doctrine and context.
"""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from aether_os.context_aware_agent import ContextAwareBaseAgent
from aether_os.llm_client import LLMProvider
from aether_os.orchestrator import ATOPhase
from aether_os.prompt_builder import get_task_template

logger = logging.getLogger(__name__)


class EMSStrategyResponse(BaseModel):
    """Structured response for EMS strategy development."""
    strategy_summary: str = Field(description="2-3 sentence strategy summary")
    objectives: List[str] = Field(description="Specific EMS objectives")
    threat_considerations: List[str] = Field(description="Key threat considerations with IDs")
    resource_requirements: List[str] = Field(description="Required resources")
    timeline: str = Field(description="Execution timeline")
    context_citations: List[str] = Field(description="Context element IDs used")
    doctrine_citations: List[str] = Field(description="Specific doctrine references")
    information_gaps: List[str] = Field(default_factory=list, description="Missing information")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level")


class ContextAwareEMSStrategyAgent(ContextAwareBaseAgent):
    """
    Context-aware EMS Strategy Agent.

    Active during Phases 1-2 (OEG and Target Development).
    Develops EMS strategy using LLM reasoning grounded in doctrine,
    threat analysis, and commander's guidance.
    """

    def __init__(self, aether_os: Any):
        """Initialize context-aware EMS Strategy Agent."""
        super().__init__(
            agent_id="ems_strategy_agent",
            aether_os=aether_os,
            role="ems_strategy",
            llm_provider=LLMProvider.ANTHROPIC,
            max_context_tokens=12000,  # Larger context for strategy
            use_semantic_tracking=True,
        )

        logger.info(f"[{self.agent_id}] Context-aware EMS Strategy Agent initialized")

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

        if phase == "PHASE1_OEG":
            return await self._develop_initial_strategy(cycle_id)
        elif phase == "PHASE2_TARGET_DEVELOPMENT":
            return await self._refine_strategy_with_targets(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase {phase}")
            return {"success": False, "reason": f"Not active in {phase}"}

    async def _develop_initial_strategy(self, cycle_id: str) -> Dict[str, Any]:
        """
        Develop initial EMS strategy during Phase 1 (OEG).

        Uses commander's guidance and threat environment to create
        comprehensive EMS strategy.
        """
        logger.info(f"[{self.agent_id}] Developing initial EMS strategy")

        # Build task from current context
        task = """Develop an electromagnetic spectrum (EMS) strategy based on:

1. Commander's intent and guidance (from context)
2. Threat environment assessment
3. Available EMS capabilities
4. Air component objectives

Your strategy must:
- Prioritize force protection and mission success
- Consider EA (Electronic Attack), EP (Electronic Protection), and ES (Electronic Warfare Support) holistically
- Identify specific EMS objectives and desired effects
- Align with USAF doctrine and procedures
- Address all critical threats

Provide comprehensive strategy with doctrine grounding."""

        # Generate strategy with LLM
        response = self.generate_with_context(
            task_description=task,
            output_schema=EMSStrategyResponse,
            temperature=0.4,  # Slightly higher for creative strategy
            max_tokens=4000,
        )

        if response["success"]:
            logger.info(
                f"[{self.agent_id}] Strategy developed: "
                f"{response.get('context_utilization', 0):.1%} context utilization"
            )

            # Store strategy in artifacts
            if "content" in response:
                self.artifacts["ems_strategy"] = response["content"]
                self.artifacts["strategy_cycle_id"] = cycle_id

        return response

    async def _refine_strategy_with_targets(self, cycle_id: str) -> Dict[str, Any]:
        """
        Refine strategy during Phase 2 with target information.

        Incorporates target development into EMS strategy.
        """
        logger.info(f"[{self.agent_id}] Refining strategy with target information")

        # Check for existing strategy
        if "ems_strategy" not in self.artifacts:
            logger.warning(f"[{self.agent_id}] No initial strategy found, creating new")
            return await self._develop_initial_strategy(cycle_id)

        task = """Refine the EMS strategy based on target development:

1. Review existing EMS strategy (from previous phase)
2. Incorporate new target information
3. Identify specific EMS requirements for each target
4. Update resource requirements
5. Ensure strategy supports target prosecution

Your refined strategy must:
- Maintain alignment with commander's guidance
- Address EMS requirements for all targets
- Update timing and coordination requirements
- Cite relevant doctrine and previous strategy elements"""

        response = self.generate_with_context(
            task_description=task,
            output_schema=EMSStrategyResponse,
            temperature=0.3,
            max_tokens=4000,
        )

        if response["success"]:
            # Update strategy
            self.artifacts["ems_strategy_refined"] = response.get("content")

        return response

    def develop_strategy(
        self,
        commanders_guidance: str,
        mission_objectives: List[str],
        timeline: str = "72 hours",
    ) -> Dict[str, Any]:
        """
        Develop EMS strategy from commander's guidance.

        Args:
            commanders_guidance: Commander's intent and guidance
            mission_objectives: List of mission objectives
            timeline: Strategy timeline

        Returns:
            Strategy response with doctrine grounding
        """
        task = get_task_template(
            "develop_strategy",
            objectives="\n".join(f"- {obj}" for obj in mission_objectives),
            guidance=commanders_guidance,
            timeline=timeline,
        )

        response = self.generate_with_context(
            task_description=task,
            output_schema=EMSStrategyResponse,
            temperature=0.4,
            max_tokens=4000,
        )

        return response

    def validate_strategy_doctrine_compliance(
        self,
        strategy: str,
    ) -> Dict[str, Any]:
        """
        Validate strategy against doctrine.

        Args:
            strategy: Strategy text to validate

        Returns:
            Validation results with compliance assessment
        """
        return self.validate_against_doctrine(
            action="develop_ems_strategy",
            proposed_decision=strategy,
        )

    def identify_strategy_gaps(self) -> List[str]:
        """
        Identify information gaps in current strategy.

        Returns:
            List of missing information items
        """
        required_info = [
            "commander's guidance",
            "threat environment",
            "available ems assets",
            "air component objectives",
            "coordination requirements",
        ]

        return self.identify_information_gaps(
            task="develop comprehensive EMS strategy",
            required_information=required_info,
        )

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

        if message_type == "develop_strategy":
            return self.develop_strategy(
                commanders_guidance=payload.get("guidance", ""),
                mission_objectives=payload.get("objectives", []),
                timeline=payload.get("timeline", "72 hours"),
            )

        elif message_type == "validate_strategy":
            return self.validate_strategy_doctrine_compliance(
                strategy=payload.get("strategy", ""),
            )

        elif message_type == "identify_gaps":
            gaps = self.identify_strategy_gaps()
            return {
                "success": True,
                "information_gaps": gaps,
                "message": f"Identified {len(gaps)} information gaps",
            }

        else:
            # Use context-aware message processing
            return self.process_message_with_context(message_type, payload)
