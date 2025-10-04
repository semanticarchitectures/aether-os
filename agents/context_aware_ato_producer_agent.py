"""
Context-Aware ATO Producer Agent for Aether OS.

Integrates EMS into Air Tasking Order with LLM-powered validation
and integration grounded in doctrine and mission requirements.
"""

import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from aether_os.context_aware_agent import ContextAwareBaseAgent
from aether_os.llm_client import LLMProvider
from aether_os.orchestrator import ATOPhase
from aether_os.prompt_builder import get_task_template

logger = logging.getLogger(__name__)


class MissionApproval(BaseModel):
    """Individual mission approval status."""
    mission_id: str
    mission_type: str
    approved: bool
    approval_required: bool
    approval_authority: Optional[str] = None
    notes: str


class StrikeIntegration(BaseModel):
    """Strike package integration details."""
    package_id: str
    ems_missions: List[str] = Field(description="EMS mission IDs in package")
    strike_elements: List[str] = Field(description="Kinetic strike elements")
    timing_coordination: str
    integration_notes: str


class ATOProducerResponse(BaseModel):
    """Structured response for ATO production."""
    ato_version: str = Field(description="ATO document version")
    mission_approvals: List[MissionApproval] = Field(description="Mission approval status")
    strike_integrations: List[StrikeIntegration] = Field(description="Strike package integrations")
    spins_sections: Dict[str, str] = Field(description="SPINS annex sections")
    validation_results: Dict[str, bool] = Field(description="Validation checks")
    completeness_check: bool = Field(description="ATO is complete")
    context_citations: List[str] = Field(description="Context element IDs used")
    doctrine_citations: List[str] = Field(description="Specific doctrine references")
    information_gaps: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class ContextAwareATOProducerAgent(ContextAwareBaseAgent):
    """
    Context-aware ATO Producer Agent.

    Active during Phase 4 (ATO Production).
    Integrates EMS missions into Air Tasking Order using LLM reasoning
    grounded in doctrine, mission plans, and integration requirements.
    """

    def __init__(self, aether_os: Any):
        """Initialize context-aware ATO Producer Agent."""
        super().__init__(
            agent_id="ato_producer_agent",
            aether_os=aether_os,
            role="ato_producer",
            llm_provider=LLMProvider.ANTHROPIC,
            max_context_tokens=14000,  # Large context for ATO integration
            use_semantic_tracking=True,
        )

        logger.info(f"[{self.agent_id}] Context-aware ATO Producer Agent initialized")

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

        if phase == "PHASE4_ATO_PRODUCTION":
            return await self._produce_ato_document(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase {phase}")
            return {"success": False, "reason": f"Not active in {phase}"}

    async def _produce_ato_document(self, cycle_id: str) -> Dict[str, Any]:
        """
        Produce ATO document during Phase 4.

        Collects EMS mission plans, validates approvals, integrates with
        strike packages, and generates SPINS annex.
        """
        logger.info(f"[{self.agent_id}] Producing ATO document")

        task = """Produce Air Tasking Order (ATO) EMS annex:

1. Review all EMS missions from Phase 3 (from context)
2. Validate mission approvals per doctrine
3. Integrate EMS missions with kinetic strike packages
4. Generate SPINS (Special Instructions) annex
5. Validate ATO completeness

Your ATO production must:
- Ensure all EA missions have required command approval
- Coordinate EMS timing with strike packages
- Prevent EA/SIGINT fratricide
- Include all frequency allocations in SPINS
- Follow ATO production doctrine
- Verify all critical missions are included
- Document integration rationale

Provide comprehensive ATO document with validation results."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=ATOProducerResponse,
            temperature=0.2,  # Low temp for precise ATO production
            max_tokens=5000,
        )

        if response["success"]:
            logger.info(
                f"[{self.agent_id}] ATO produced: "
                f"{response.get('context_utilization', 0):.1%} context utilization"
            )

            # Store ATO document
            self.artifacts["ato_document"] = response.get("content")
            self.artifacts["ato_cycle_id"] = cycle_id

        return response

    def produce_ato_ems_annex(
        self,
        ew_missions: List[Dict[str, Any]],
        frequency_allocations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Produce ATO EMS annex from missions and allocations.

        Args:
            ew_missions: EW missions from Phase 3
            frequency_allocations: Frequency allocations from Spectrum Manager

        Returns:
            ATO EMS annex with integrations and SPINS
        """
        missions_str = "\n".join([
            f"- Mission {m.get('mission_id')}: {m.get('mission_type')} targeting {m.get('target_id', 'unspecified')}"
            for m in ew_missions
        ])

        allocations_str = "\n".join([
            f"- {a.get('mission_id')}: {a.get('frequency_min_mhz')}-{a.get('frequency_max_mhz')} MHz, {a.get('start_time')} to {a.get('end_time')}"
            for a in frequency_allocations
        ])

        task = f"""Produce ATO EMS annex integrating these missions and allocations:

EW MISSIONS:
{missions_str}

FREQUENCY ALLOCATIONS:
{allocations_str}

Requirements:
1. Validate all missions have proper approvals
2. Integrate with strike packages (from context)
3. Generate SPINS annex with:
   - Frequency management procedures
   - EA/EP/ES coordination procedures
   - Emergency procedures
4. Ensure timing coordination
5. Check for mission conflicts
6. Cite relevant ATO production doctrine

Provide complete ATO EMS annex."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=ATOProducerResponse,
            temperature=0.2,
            max_tokens=5000,
        )

        return response

    def validate_mission_approvals(
        self,
        missions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate mission approvals against doctrine.

        Args:
            missions: List of missions to validate

        Returns:
            Validation results with approval status
        """
        missions_str = "\n".join([
            f"- {m.get('mission_id')}: {m.get('mission_type')}, approved: {m.get('approved', False)}"
            for m in missions
        ])

        task = f"""Validate mission approvals per doctrine:

MISSIONS:
{missions_str}

Approval requirements:
1. EA missions require command approval (O-6 or higher per doctrine)
2. SEAD missions require operational approval
3. Spectrum allocations above certain power require coordination
4. Cross-border operations require additional approval

For each mission:
- Determine if approval is required
- Check if approval is present
- Identify approval authority level needed
- Flag unapproved missions

Cite specific doctrine requirements for approval levels."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=ATOProducerResponse,
            temperature=0.2,
            max_tokens=4000,
        )

        return response

    def integrate_ems_with_strikes(
        self,
        ew_missions: List[Dict[str, Any]],
        strike_packages: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Integrate EMS missions with kinetic strike packages.

        Args:
            ew_missions: EW missions to integrate
            strike_packages: Strike packages requiring EMS support

        Returns:
            Integration plan with timing coordination
        """
        missions_str = "\n".join([
            f"- {m.get('mission_id')}: {m.get('mission_type')}, TOA: {m.get('toa', 'unspecified')}"
            for m in ew_missions
        ])

        strike_str = ""
        if strike_packages:
            strike_str = "\nSTRIKE PACKAGES:\n" + "\n".join([
                f"- {p.get('package_id')}: targets {p.get('targets')}, TOA: {p.get('toa')}"
                for p in strike_packages
            ])

        task = f"""Integrate EMS missions with strike packages:

EW MISSIONS:
{missions_str}
{strike_str}

Integration requirements:
1. EA jamming must start before strike TOA (typically H-5 to H-hour)
2. Coordinate standoff vs stand-in jamming based on threat
3. Ensure jamming doesn't interfere with strike communications
4. Synchronize timing for maximum effectiveness
5. Identify which strikes require EA support
6. Follow integration doctrine

Provide detailed integration plan with timing coordination."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=ATOProducerResponse,
            temperature=0.3,
            max_tokens=4000,
        )

        return response

    def generate_spins_annex(
        self,
        missions: List[Dict[str, Any]],
        allocations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate SPINS (Special Instructions) annex for EMS.

        Args:
            missions: EMS missions
            allocations: Frequency allocations

        Returns:
            SPINS annex with procedures
        """
        task = f"""Generate SPINS annex for EMS operations:

Based on {len(missions)} missions and {len(allocations)} frequency allocations.

SPINS annex must include:
1. Frequency Management
   - Allocated frequency bands
   - Coordination procedures
   - Emergency reallocation procedures

2. EA Procedures
   - Jamming restrictions (no friendly IFF, GPS)
   - SIGINT coordination (prevent fratricide)
   - Jamming profiles and power settings

3. EP Procedures
   - Anti-jam settings
   - GPS protection modes
   - Communications security

4. ES Procedures
   - Collection coordination
   - SIGINT product delivery

5. Emergency Procedures
   - Spectrum conflicts
   - Emergency shutdown procedures
   - Alternate frequencies

Cite relevant SPINS doctrine and procedures."""

        response = self.generate_with_context(
            task_description=task,
            output_schema=ATOProducerResponse,
            temperature=0.25,
            max_tokens=4000,
        )

        return response

    def validate_ato_completeness(
        self,
        ato_document: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate ATO completeness.

        Args:
            ato_document: ATO document to validate

        Returns:
            Validation results
        """
        task = """Validate ATO completeness:

Check that ATO includes:
1. All approved EMS missions
2. All frequency allocations
3. Complete SPINS annex
4. Strike package integrations
5. Timing coordination
6. Emergency procedures
7. All required approvals

Identify any gaps or missing elements.
Cite ATO production doctrine requirements."""

        response = self.generate_with_context(
            task_description=task,
            temperature=0.2,
            max_tokens=3000,
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

        if message_type == "produce_ato":
            return self.produce_ato_ems_annex(
                ew_missions=payload.get("ew_missions", []),
                frequency_allocations=payload.get("frequency_allocations", []),
            )

        elif message_type == "validate_approvals":
            return self.validate_mission_approvals(
                missions=payload.get("missions", []),
            )

        elif message_type == "integrate_strikes":
            return self.integrate_ems_with_strikes(
                ew_missions=payload.get("ew_missions", []),
                strike_packages=payload.get("strike_packages"),
            )

        elif message_type == "generate_spins":
            return self.generate_spins_annex(
                missions=payload.get("missions", []),
                allocations=payload.get("allocations", []),
            )

        elif message_type == "validate_completeness":
            return self.validate_ato_completeness(
                ato_document=payload.get("ato_document", {}),
            )

        else:
            # Use context-aware message processing
            return self.process_message_with_context(message_type, payload)
