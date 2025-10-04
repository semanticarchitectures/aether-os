"""
ATO Producer Agent for Aether OS.

Integrates EMS into Air Tasking Order during Phase 4 (ATO Production).
"""

from typing import Dict, Any, List, Optional
import logging

from agents.base_agent import BaseAetherAgent
from aether_os.access_control import InformationCategory

logger = logging.getLogger(__name__)


class ATOProducerAgent(BaseAetherAgent):
    """
    ATO Producer Agent.

    Active Phases: Phase 4 (ATO Production)
    Role: Integrates EMS into Air Tasking Order
    Access Level: SENSITIVE
    """

    def __init__(self, aether_os: Any):
        """Initialize ATO Producer Agent."""
        super().__init__(agent_id="ato_producer_agent", aether_os=aether_os)

    async def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """Execute tasks for the current phase."""
        if phase == "PHASE4_ATO_PRODUCTION":
            return await self._execute_phase4(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase: {phase}")
            return {}

    async def _execute_phase4(self, cycle_id: str) -> Dict[str, Any]:
        """
        Execute Phase 4 (ATO Production) tasks.

        Integrate EMS missions into ATO.
        """
        logger.info(f"[{self.agent_id}] Executing Phase 4 (ATO Production) for cycle {cycle_id}")

        outputs = {}

        # Produce ATO EMS annex
        ato_annex = self.execute_doctrinal_procedure(
            procedure_name="Produce ATO EMS Annex",
            procedure_fn=self.produce_ato_ems_annex,
            expected_time_hours=3.0,
            cycle_id=cycle_id,
            phase="PHASE4_ATO_PRODUCTION",
        )

        outputs["ato_ems_annex"] = ato_annex

        # Record output
        self.aether_os.orchestrator.record_output("ato_document", ato_annex)

        return outputs

    def produce_ato_ems_annex(self, cycle_id: str) -> Dict[str, Any]:
        """
        Produce ATO EMS annex.

        Integrates EMS missions into the Air Tasking Order.
        """
        logger.info(f"[{self.agent_id}] Producing ATO EMS annex...")

        # Get EW missions from Phase 3
        current_cycle = self.aether_os.orchestrator.current_cycle
        if not current_cycle or "ew_missions" not in current_cycle.outputs:
            logger.warning("No EW missions available")
            self.flag_information_gap(
                workflow_name="Produce ATO EMS Annex",
                missing_information="EW missions from Phase 3",
                cycle_id=cycle_id,
                phase="PHASE4_ATO_PRODUCTION",
            )
            ew_missions = []
        else:
            ew_missions = current_cycle.outputs["ew_missions"]

        # Get frequency allocations
        if "frequency_allocations" in current_cycle.outputs:
            frequency_allocations = current_cycle.outputs["frequency_allocations"]
        else:
            frequency_allocations = []

        # Validate mission approvals
        validation_result = self.execute_doctrinal_procedure(
            procedure_name="Validate Mission Approvals",
            procedure_fn=self._validate_mission_approvals,
            expected_time_hours=1.0,
            cycle_id=cycle_id,
            phase="PHASE4_ATO_PRODUCTION",
            ew_missions=ew_missions,
        )

        if not validation_result["all_approved"]:
            logger.warning(f"{len(validation_result['unapproved'])} missions lack approval")

        # Integrate with kinetic strikes
        integration = self._integrate_ems_with_strikes(ew_missions)

        # Generate SPINS annex (Special Instructions)
        spins_annex = self._generate_spins_annex(ew_missions, frequency_allocations)

        ato_annex = {
            "cycle_id": cycle_id,
            "ems_missions": ew_missions,
            "frequency_allocations": frequency_allocations,
            "validation": validation_result,
            "strike_integration": integration,
            "spins_annex": spins_annex,
            "status": "published",
        }

        logger.info(f"[{self.agent_id}] ATO EMS annex produced with {len(ew_missions)} missions")

        return ato_annex

    def _validate_mission_approvals(
        self,
        ew_missions: List[Dict[str, Any]],
        cycle_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate that all missions have required approvals.

        Per doctrine, certain missions require command approval.

        Args:
            ew_missions: List of EW missions to validate
            cycle_id: Optional ATO cycle ID
        """
        logger.info(f"[{self.agent_id}] Validating approvals for {len(ew_missions)} missions")

        unapproved = []

        for mission in ew_missions:
            # Check if EA mission (requires approval)
            if mission.get("mission_type") == "EA":
                if not mission.get("approved"):
                    logger.warning(f"EA mission {mission['mission_id']} lacks approval")
                    unapproved.append(mission["mission_id"])

                    # Escalate for approval
                    decision = self.escalate_for_human_decision(
                        decision_type="ea_mission_approval",
                        context={
                            "mission_id": mission["mission_id"],
                            "mission_type": mission["mission_type"],
                            "objectives": mission.get("objectives"),
                        },
                        reason="EA mission requires command approval per doctrine",
                    )

                    if decision.get("approved"):
                        mission["approved"] = True
                        mission["approved_by"] = decision.get("human_operator")

        return {
            "all_approved": len(unapproved) == 0,
            "unapproved": unapproved,
            "total_missions": len(ew_missions),
        }

    def _integrate_ems_with_strikes(
        self,
        ew_missions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Integrate EMS missions with kinetic strike packages.

        EA missions typically support SEAD and penetrating strikes.
        """
        logger.info(f"[{self.agent_id}] Integrating {len(ew_missions)} EMS missions with strikes")

        # In production, would coordinate with kinetic strike planners
        # For prototype, simplified integration

        strike_packages = []

        for mission in ew_missions:
            if mission.get("mission_type") == "EA":
                # EA typically supports strikes
                strike_packages.append({
                    "package_id": f"PKG-{mission['mission_id']}",
                    "ems_support": mission["mission_id"],
                    "strike_elements": ["Placeholder kinetic strikes"],
                    "integration": "EA provides SEAD for strike package",
                })

        return {
            "strike_packages": strike_packages,
            "total_packages": len(strike_packages),
        }

    def _generate_spins_annex(
        self,
        ew_missions: List[Dict[str, Any]],
        frequency_allocations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate SPINS (Special Instructions) annex for EMS.

        SPINS provide specific operating instructions for EMS operations.
        """
        logger.info(f"[{self.agent_id}] Generating SPINS annex")

        spins = {
            "ems_spins_version": "1.0",
            "effective_time": "ATO Day",
            "frequency_management": {
                "allocated_bands": [
                    f"{alloc['frequency_min_mhz']}-{alloc['frequency_max_mhz']} MHz"
                    for alloc in frequency_allocations
                ],
                "coordination_procedures": "Coordinate via spectrum manager on guard frequency",
            },
            "ea_procedures": {
                "jamming_restrictions": "Do not jam friendly IFF frequencies",
                "coordination": "Coordinate jamming with SIGINT collection",
            },
            "ep_procedures": {
                "anti_jam_settings": "GPS anti-jam mode AUTO for all platforms",
            },
            "emergency_procedures": {
                "spectrum_conflicts": "Contact spectrum manager immediately on emergency freq",
                "ea_shutdown": "Cease jamming on command 'STOPJAM'",
            },
        }

        return spins
