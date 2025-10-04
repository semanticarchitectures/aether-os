"""
Context-Aware EW Planner Agent for Aether OS.

Plans Electronic Warfare missions with LLM-powered reasoning
grounded in doctrine, threat analysis, and asset capabilities.
"""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from aether_os.context_aware_agent import ContextAwareBaseAgent
from aether_os.llm_client import LLMProvider
from aether_os.orchestrator import ATOPhase
from aether_os.prompt_builder import get_task_template

logger = logging.getLogger(__name__)


class MissionPlan(BaseModel):
    """Individual EW mission plan."""
    mission_id: str
    target_id: str
    asset_id: str
    mission_type: str  # SEAD, escort, standoff, etc.
    toa: str  # Time Over Target
    frequency_request: Optional[str] = None
    coordination_notes: str


class EWMissionPlanResponse(BaseModel):
    """Structured response for EW mission planning."""
    missions: List[MissionPlan] = Field(description="Planned EW missions")
    asset_assignments: Dict[str, str] = Field(description="Asset to target mapping")
    frequency_requests: List[str] = Field(description="Frequency allocation requests")
    fratricide_checks: List[str] = Field(description="EA/SIGINT fratricide checks performed")
    coordination_requirements: List[str] = Field(description="Required coordination")
    context_citations: List[str] = Field(description="Context element IDs used")
    doctrine_citations: List[str] = Field(description="Specific doctrine references")
    information_gaps: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ContextAwareEWPlannerAgent(ContextAwareBaseAgent):
    """
    Context-aware EW Planner Agent.

    Active during Phase 3 (Weaponeering).
    Plans EW missions using LLM reasoning grounded in doctrine,
    threat analysis, asset capabilities, and EMS strategy.
    """

    def __init__(self, aether_os: Any):
        """Initialize context-aware EW Planner Agent."""
        super().__init__(
            agent_id="ew_planner_agent",
            aether_os=aether_os,
            role="ew_planner",
            llm_provider=LLMProvider.ANTHROPIC,
            max_context_tokens=16000,  # Large context for mission planning
            use_semantic_tracking=True,
        )

        logger.info(f"[{self.agent_id}] Context-aware EW Planner Agent initialized")

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

        if phase == "PHASE3_WEAPONEERING":
            return await self._plan_ew_missions(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase {phase}")
            return {"success": False, "reason": f"Not active in {phase}"}

    async def _plan_ew_missions(self, cycle_id: str) -> Dict[str, Any]:
        """
        Plan EW missions during Phase 3 (Weaponeering).

        Uses threat analysis, available assets, and EMS strategy
        to create detailed mission plans.
        """
        logger.info(f"[{self.agent_id}] Planning EW missions")

        task = """Plan Electronic Warfare missions based on:

1. EMS strategy objectives (from previous phases)
2. Threat environment and target priorities
3. Available EMS assets and capabilities
4. Strike package coordination requirements

Your mission plan must:
- Assign appropriate assets to targets based on capability and range
- Request frequency allocations from Spectrum Manager
- Check for EA/SIGINT fratricide (friendly jamming vs friendly signals)
- Coordinate timing with strike packages
- Follow USAF EW planning doctrine
- Ensure all critical threats are addressed

For each mission:
- Specify target, asset, mission type, and timing
- Identify required frequencies
- Note coordination requirements
- Cite relevant doctrine and context"""

        response = self.generate_with_context(
            task_description=task,
            output_schema=EWMissionPlanResponse,
            temperature=0.3,
            max_tokens=5000,
        )

        if response["success"]:
            logger.info(
                f"[{self.agent_id}] Mission plan created: "
                f"{response.get('context_utilization', 0):.1%} context utilization"
            )

            # Store mission plan
            self.artifacts["ew_mission_plan"] = response.get("content")
            self.artifacts["plan_cycle_id"] = cycle_id

            # Request frequency allocations if needed
            await self._request_frequencies(response)

        return response

    async def _request_frequencies(self, mission_plan: Dict[str, Any]):
        """
        Request frequency allocations from Spectrum Manager.

        Args:
            mission_plan: Mission plan with frequency requests
        """
        # Extract frequency requests from plan
        content = mission_plan.get("content", "{}")

        try:
            import json
            plan_data = json.loads(content) if isinstance(content, str) else content

            if isinstance(plan_data, dict) and "frequency_requests" in plan_data:
                requests = plan_data["frequency_requests"]

                if requests:
                    logger.info(
                        f"[{self.agent_id}] Requesting {len(requests)} frequency allocations"
                    )

                    # Send requests to Spectrum Manager
                    # (Would integrate with actual spectrum manager agent)
                    self.artifacts["pending_frequency_requests"] = requests

        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to parse frequency requests: {e}")

    def plan_missions(
        self,
        mission_type: str,
        targets: List[str],
        timeframe: str,
        strike_packages: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Plan EW missions for specific targets.

        Args:
            mission_type: Type of mission (SEAD, escort, etc.)
            targets: Target IDs to plan missions for
            timeframe: Mission timeframe
            strike_packages: Strike packages requiring coordination

        Returns:
            Mission plan with asset assignments
        """
        # Build strike package info
        strike_info = ""
        if strike_packages:
            strike_info = "\nStrike Packages:\n"
            for pkg in strike_packages:
                strike_info += f"- {pkg.get('name')}: targets {pkg.get('targets')}, TOA {pkg.get('toa')}\n"

        task = get_task_template(
            "plan_missions",
            mission_type=mission_type,
            targets=", ".join(targets),
            timeframe=timeframe,
        ) + strike_info

        response = self.generate_with_context(
            task_description=task,
            output_schema=EWMissionPlanResponse,
            temperature=0.3,
            max_tokens=5000,
        )

        return response

    def check_fratricide(
        self,
        proposed_missions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Check for EA/SIGINT fratricide in mission plans.

        Args:
            proposed_missions: List of proposed EW missions

        Returns:
            Fratricide check results
        """
        missions_str = "\n".join([
            f"- {m.get('mission_id')}: {m.get('asset_id')} jamming {m.get('target_id')}"
            for m in proposed_missions
        ])

        task = f"""Check for EA/SIGINT fratricide in these EW missions:

{missions_str}

Fratricide check requirements:
1. Verify jamming will not interfere with friendly SIGINT collection
2. Check for conflicts with friendly communications
3. Identify timing deconfliction requirements
4. Cite relevant doctrine on fratricide prevention

Provide detailed fratricide assessment with recommendations."""

        response = self.generate_with_context(
            task_description=task,
            temperature=0.2,  # Lower temp for safety checks
            max_tokens=3000,
        )

        return response

    def assign_assets_to_targets(
        self,
        targets: List[Dict[str, Any]],
        available_assets: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Assign EMS assets to targets based on capability and range.

        Args:
            targets: List of targets with requirements
            available_assets: List of available EMS assets

        Returns:
            Asset assignment recommendations
        """
        targets_str = "\n".join([
            f"- {t.get('threat_id')}: {t.get('threat_type')} at ({t.get('location', {}).get('lat')}, {t.get('location', {}).get('lon')}), priority: {t.get('priority')}"
            for t in targets
        ])

        assets_str = "\n".join([
            f"- {a.get('asset_id')}: {a.get('platform')} - {a.get('capability')}, range: {a.get('effective_range_nm', 'N/A')}nm"
            for a in available_assets
        ])

        task = f"""Assign EMS assets to targets based on capability and range:

TARGETS:
{targets_str}

AVAILABLE ASSETS:
{assets_str}

Assignment requirements:
1. Match asset capability to threat type
2. Ensure asset range covers target location
3. Prioritize critical threats
4. Optimize asset utilization
5. Cite doctrine on asset employment

Provide optimal asset-to-target assignments."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=EWMissionPlanResponse,
            temperature=0.3,
            max_tokens=4000,
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

        if message_type == "plan_missions":
            return self.plan_missions(
                mission_type=payload.get("mission_type", "SEAD"),
                targets=payload.get("targets", []),
                timeframe=payload.get("timeframe", "H-hour to H+4"),
                strike_packages=payload.get("strike_packages"),
            )

        elif message_type == "check_fratricide":
            return self.check_fratricide(
                proposed_missions=payload.get("missions", []),
            )

        elif message_type == "assign_assets":
            return self.assign_assets_to_targets(
                targets=payload.get("targets", []),
                available_assets=payload.get("assets", []),
            )

        else:
            # Use context-aware message processing
            return self.process_message_with_context(message_type, payload)
