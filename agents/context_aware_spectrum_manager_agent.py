"""
Context-Aware Spectrum Manager Agent for Aether OS.

Manages frequency allocation and deconfliction with LLM-powered reasoning
grounded in doctrine, spectrum status, and JCEOI procedures.
"""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from aether_os.context_aware_agent import ContextAwareBaseAgent
from aether_os.llm_client import LLMProvider
from aether_os.orchestrator import ATOPhase
from aether_os.prompt_builder import get_task_template

logger = logging.getLogger(__name__)


class FrequencyAllocation(BaseModel):
    """Individual frequency allocation."""
    mission_id: str
    frequency_min_mhz: float
    frequency_max_mhz: float
    start_time: str
    end_time: str
    geographic_area: Optional[str] = None
    notes: str


class SpectrumAllocationResponse(BaseModel):
    """Structured response for spectrum allocation."""
    allocations: List[FrequencyAllocation] = Field(description="Frequency allocations")
    conflicts_identified: List[str] = Field(description="Spectrum conflicts found")
    deconfliction_actions: List[str] = Field(description="Deconfliction actions taken")
    coordination_required: List[str] = Field(description="Required coordination")
    jceoi_compliance: bool = Field(description="Follows JCEOI process")
    context_citations: List[str] = Field(description="Context element IDs used")
    doctrine_citations: List[str] = Field(description="Specific doctrine references")
    information_gaps: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ContextAwareSpectrumManagerAgent(ContextAwareBaseAgent):
    """
    Context-aware Spectrum Manager Agent.

    Active during Phases 3 and 5 (Weaponeering and Execution).
    Manages frequency allocation and deconfliction using LLM reasoning
    grounded in doctrine, spectrum status, and JCEOI procedures.
    """

    def __init__(self, aether_os: Any):
        """Initialize context-aware Spectrum Manager Agent."""
        super().__init__(
            agent_id="spectrum_manager_agent",
            aether_os=aether_os,
            role="spectrum_manager",
            llm_provider=LLMProvider.ANTHROPIC,
            max_context_tokens=12000,
            use_semantic_tracking=True,
        )

        logger.info(f"[{self.agent_id}] Context-aware Spectrum Manager Agent initialized")

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
            return await self._allocate_planning_frequencies(cycle_id)
        elif phase == "PHASE5_EXECUTION":
            return await self._manage_execution_spectrum(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase {phase}")
            return {"success": False, "reason": f"Not active in {phase}"}

    async def _allocate_planning_frequencies(self, cycle_id: str) -> Dict[str, Any]:
        """
        Allocate frequencies during Phase 3 (Weaponeering).

        Processes frequency requests from EW Planner and other users,
        deconflicts spectrum usage, and creates allocations.
        """
        logger.info(f"[{self.agent_id}] Allocating frequencies for planning")

        task = """Process frequency allocation requests:

1. Review all pending frequency requests (from context)
2. Check for conflicts with existing allocations
3. Follow JCEOI (Joint Communications-Electronics Operating Instructions) process
4. Prioritize by mission criticality
5. Coordinate with other spectrum users to deconflict
6. Create frequency allocations

Your allocations must:
- Prevent fratricide and interference
- Follow spectrum management doctrine
- Document all deconfliction actions
- Ensure all critical missions receive frequencies
- Cite relevant JCEOI procedures and doctrine

Provide detailed allocation plan with deconfliction rationale."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=SpectrumAllocationResponse,
            temperature=0.2,  # Low temp for precise allocations
            max_tokens=4000,
        )

        if response["success"]:
            logger.info(
                f"[{self.agent_id}] Allocations created: "
                f"{response.get('context_utilization', 0):.1%} context utilization"
            )

            # Store allocations
            self.artifacts["frequency_allocations"] = response.get("content")
            self.artifacts["allocation_cycle_id"] = cycle_id

        return response

    async def _manage_execution_spectrum(self, cycle_id: str) -> Dict[str, Any]:
        """
        Manage spectrum during Phase 5 (Execution).

        Handles real-time spectrum management, emergency reallocations,
        and coordination during mission execution.
        """
        logger.info(f"[{self.agent_id}] Managing execution spectrum")

        task = """Manage spectrum during mission execution:

1. Monitor active frequency allocations
2. Handle emergency reallocation requests
3. Coordinate real-time deconfliction
4. Track spectrum usage and conflicts
5. Maintain situational awareness

Your management must:
- Respond rapidly to urgent requests
- Prevent interference with active missions
- Follow emergency procedures
- Document all changes
- Cite relevant doctrine

Provide execution spectrum status and actions."""

        response = self.generate_with_context(
            task_description=task,
            temperature=0.25,
            max_tokens=3000,
        )

        return response

    def allocate_frequencies(
        self,
        requests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Allocate frequencies for mission requests.

        Args:
            requests: List of frequency requests with mission details

        Returns:
            Allocation response with frequencies assigned
        """
        requests_str = "\n".join([
            f"- Mission {r.get('mission_id')}: {r.get('band', 'unspecified')} band, priority: {r.get('priority', 'medium')}"
            for r in requests
        ])

        task = get_task_template(
            "allocate_frequencies",
            requests=requests_str,
        )

        response = self.generate_with_context(
            task_description=task,
            output_schema=SpectrumAllocationResponse,
            temperature=0.2,
            max_tokens=4000,
        )

        return response

    def check_conflicts(
        self,
        proposed_allocation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Check for spectrum conflicts with proposed allocation.

        Args:
            proposed_allocation: Proposed frequency allocation

        Returns:
            Conflict check results
        """
        task = f"""Check for spectrum conflicts:

Proposed Allocation:
- Frequency: {proposed_allocation.get('frequency_min_mhz')}-{proposed_allocation.get('frequency_max_mhz')} MHz
- Time: {proposed_allocation.get('start_time')} to {proposed_allocation.get('end_time')}
- Area: {proposed_allocation.get('geographic_area', 'unspecified')}
- Mission: {proposed_allocation.get('mission_id')}

Conflict check requirements:
1. Check against existing allocations (from context)
2. Identify overlapping frequencies, times, or areas
3. Assess interference potential
4. Recommend deconfliction actions if conflicts found
5. Cite relevant spectrum management procedures

Provide detailed conflict analysis."""

        response = self.generate_with_context(
            task_description=task,
            temperature=0.2,
            max_tokens=3000,
        )

        return response

    def coordinate_deconfliction(
        self,
        conflicts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Coordinate deconfliction for spectrum conflicts.

        Args:
            conflicts: List of identified conflicts

        Returns:
            Deconfliction plan
        """
        conflicts_str = "\n".join([
            f"- Conflict {i+1}: {c.get('description', str(c))}"
            for i, c in enumerate(conflicts)
        ])

        task = f"""Coordinate spectrum deconfliction:

Identified Conflicts:
{conflicts_str}

Deconfliction requirements:
1. Prioritize by mission criticality
2. Propose frequency, time, or geographic separation
3. Coordinate with affected users
4. Follow JCEOI deconfliction procedures
5. Ensure no mission is left without spectrum

Provide comprehensive deconfliction plan with coordination actions."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=SpectrumAllocationResponse,
            temperature=0.3,
            max_tokens=4000,
        )

        return response

    def emergency_reallocation(
        self,
        reason: str,
        affected_missions: List[str],
        urgency: str = "high",
    ) -> Dict[str, Any]:
        """
        Handle emergency frequency reallocation.

        Args:
            reason: Reason for emergency reallocation
            affected_missions: Missions requiring reallocation
            urgency: Urgency level

        Returns:
            Emergency reallocation plan
        """
        task = f"""Handle emergency frequency reallocation:

Reason: {reason}
Urgency: {urgency}
Affected Missions: {', '.join(affected_missions)}

Emergency procedures:
1. Assess immediate spectrum needs
2. Identify available frequencies
3. Reallocate with minimal mission impact
4. Coordinate rapid implementation
5. Follow emergency authorization procedures

NOTE: Emergency reallocations may require senior approval per doctrine.

Provide emergency reallocation plan with execution timeline."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=SpectrumAllocationResponse,
            temperature=0.25,
            max_tokens=3000,
            additional_instructions="This is an EMERGENCY reallocation. Prioritize rapid action while maintaining safety and doctrine compliance.",
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

        if message_type == "allocate_frequencies":
            return self.allocate_frequencies(
                requests=payload.get("requests", []),
            )

        elif message_type == "check_conflicts":
            return self.check_conflicts(
                proposed_allocation=payload.get("allocation", {}),
            )

        elif message_type == "coordinate_deconfliction":
            return self.coordinate_deconfliction(
                conflicts=payload.get("conflicts", []),
            )

        elif message_type == "emergency_reallocation":
            return self.emergency_reallocation(
                reason=payload.get("reason", "unspecified"),
                affected_missions=payload.get("affected_missions", []),
                urgency=payload.get("urgency", "high"),
            )

        else:
            # Use context-aware message processing
            return self.process_message_with_context(message_type, payload)
