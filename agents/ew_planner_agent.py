"""
EW Planner Agent for Aether OS.

Plans Electronic Warfare missions during Phase 3 (Weaponeering).
Translates EMS strategy into specific missions and coordinates spectrum allocation.
"""

from typing import Dict, Any, List
import logging

from agents.base_agent import BaseAetherAgent
from aether_os.access_control import InformationCategory

logger = logging.getLogger(__name__)


class EWPlannerAgent(BaseAetherAgent):
    """
    EW Planner Agent.

    Active Phases: Phase 3 (Weaponeering)
    Role: Plans Electronic Warfare missions
    Access Level: SENSITIVE
    """

    def __init__(self, aether_os: Any):
        """Initialize EW Planner Agent."""
        super().__init__(agent_id="ew_planner_agent", aether_os=aether_os)

    async def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """Execute tasks for the current phase."""
        if phase == "PHASE3_WEAPONEERING":
            return await self._execute_phase3(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase: {phase}")
            return {}

    async def _execute_phase3(self, cycle_id: str) -> Dict[str, Any]:
        """
        Execute Phase 3 (Weaponeering) tasks.

        Plan EW missions based on strategy and requirements.
        """
        logger.info(f"[{self.agent_id}] Executing Phase 3 (Weaponeering) for cycle {cycle_id}")

        outputs = {}

        # Plan EW missions
        missions = self.execute_doctrinal_procedure(
            procedure_name="Plan EW Missions",
            procedure_fn=self.plan_ew_missions,
            expected_time_hours=4.0,
            cycle_id=cycle_id,
            phase="PHASE3_WEAPONEERING",
        )

        outputs["ew_missions"] = missions

        # Record output
        self.aether_os.orchestrator.record_output("ew_missions", missions)

        return outputs

    def plan_ew_missions(self, cycle_id: str) -> List[Dict[str, Any]]:
        """
        Plan EW missions based on EMS strategy and requirements.

        Follows doctrine to:
        1. Review EMS strategy
        2. Identify required EA/EP/ES missions
        3. Assign assets to missions
        4. Request frequency allocations
        5. Check for fratricide
        """
        logger.info(f"[{self.agent_id}] Planning EW missions...")

        # Get EMS requirements from Phase 2
        current_cycle = self.aether_os.orchestrator.current_cycle
        if not current_cycle or "ems_requirements" not in current_cycle.outputs:
            logger.warning("No EMS requirements available")
            self.flag_information_gap(
                workflow_name="Plan EW Missions",
                missing_information="EMS requirements from Phase 2",
                cycle_id=cycle_id,
                phase="PHASE3_WEAPONEERING",
            )
            requirements = self._get_default_requirements()
        else:
            requirements = current_cycle.outputs["ems_requirements"]

        # Query available EMS assets
        assets_result = self.aether_os.query_information(
            agent_id=self.agent_id,
            category=InformationCategory.ASSET_STATUS,
            query_params={"asset_types": ["electronic_attack", "electronic_protect", "electronic_warfare_support"]},
        )

        if not assets_result.get("success"):
            logger.error("Failed to query EMS assets")
            return []

        available_assets = assets_result.get("data", [])

        # Plan missions based on requirements
        missions = []

        # EA missions
        for i, ea_req in enumerate(requirements.get("ea_requirements", []), 1):
            mission = self._create_ea_mission(
                mission_id=f"EA-{cycle_id}-{i:03d}",
                requirement=ea_req,
                available_assets=available_assets,
                cycle_id=cycle_id,
            )
            missions.append(mission)

        # EP missions
        for i, ep_req in enumerate(requirements.get("ep_requirements", []), 1):
            mission = self._create_ep_mission(
                mission_id=f"EP-{cycle_id}-{i:03d}",
                requirement=ep_req,
                available_assets=available_assets,
            )
            missions.append(mission)

        logger.info(f"[{self.agent_id}] Planned {len(missions)} EW missions")

        return missions

    def _create_ea_mission(
        self,
        mission_id: str,
        requirement: str,
        available_assets: List[Dict],
        cycle_id: str,
    ) -> Dict[str, Any]:
        """Create an Electronic Attack mission."""
        # Assign asset
        assigned_asset = None
        for asset in available_assets:
            if asset.get("asset_type") == "electronic_attack" and asset.get("status") == "available":
                assigned_asset = asset["asset_id"]
                break

        if not assigned_asset:
            logger.warning(f"No available EA asset for mission {mission_id}")
            self.aether_os.improvement_logger.flag_inefficiency(
                ato_cycle_id=cycle_id,
                phase="PHASE3_WEAPONEERING",
                agent_id=self.agent_id,
                workflow_name="Plan EW Missions",
                inefficiency_type="resource_bottleneck",
                description=f"No available EA assets for requirement: {requirement}",
                suggested_improvement="Increase EA asset allocation or adjust mission timeline",
                severity="high",
            )

        mission = {
            "mission_id": mission_id,
            "mission_type": "EA",
            "requirement": requirement,
            "assigned_asset": assigned_asset,
            "objectives": ["Suppress enemy air defenses"],
            "status": "planned",
        }

        # Request frequency allocation
        if assigned_asset:
            self._request_frequency_allocation(mission, cycle_id)

            # Check for EA/SIGINT fratricide
            fratricide_check = self._check_ea_sigint_fratricide(mission)
            mission["fratricide_check"] = fratricide_check

        return mission

    def _create_ep_mission(
        self,
        mission_id: str,
        requirement: str,
        available_assets: List[Dict],
    ) -> Dict[str, Any]:
        """Create an Electronic Protect mission."""
        # Assign asset
        assigned_asset = None
        for asset in available_assets:
            if asset.get("capabilities") and "protection" in asset.get("capabilities", []):
                assigned_asset = asset["asset_id"]
                break

        mission = {
            "mission_id": mission_id,
            "mission_type": "EP",
            "requirement": requirement,
            "assigned_asset": assigned_asset,
            "objectives": ["Protect friendly communications"],
            "status": "planned",
        }

        return mission

    def _request_frequency_allocation(
        self,
        mission: Dict[str, Any],
        cycle_id: str,
    ) -> None:
        """
        Request frequency allocation from Spectrum Manager.

        This is inter-agent communication.
        """
        logger.info(
            f"[{self.agent_id}] Requesting frequency for mission {mission['mission_id']}"
        )

        # Prepare frequency request
        frequency_request = {
            "mission_id": mission["mission_id"],
            "frequency_range": (2400.0, 2500.0),  # Example S-band
            "time_window": ("2025-10-04T10:00:00Z", "2025-10-04T14:00:00Z"),
            "geographic_area": {
                "type": "Polygon",
                "coordinates": [[[44.0, 33.0], [45.0, 33.0], [45.0, 34.0], [44.0, 34.0], [44.0, 33.0]]],
            },
            "priority": "high",
        }

        # Send to Spectrum Manager (async in production)
        # For now, add to spectrum manager's queue directly
        import asyncio

        async def send_request():
            response = await self.aether_os.send_agent_message(
                from_agent=self.agent_id,
                to_agent="spectrum_manager_agent",
                message_type="frequency_request",
                payload=frequency_request,
            )
            return response

        # In prototype, just log
        logger.info(f"Frequency request sent for mission {mission['mission_id']}")
        mission["frequency_requested"] = True

    def _check_ea_sigint_fratricide(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for Electronic Attack / SIGINT fratricide.

        Per doctrine, EA jamming can interfere with SIGINT collection.
        """
        logger.info(
            f"[{self.agent_id}] Checking EA/SIGINT fratricide for mission {mission['mission_id']}"
        )

        # In production, would check SIGINT collection plans
        # For prototype, simplified check

        fratricide_risk = {
            "risk_level": "low",
            "conflicts": [],
            "mitigation": "Coordinate jamming timeline with SIGINT collection windows",
        }

        return fratricide_risk

    def _get_default_requirements(self) -> Dict[str, Any]:
        """Get default EMS requirements as fallback."""
        return {
            "ea_requirements": ["Basic SEAD support"],
            "ep_requirements": ["Communications protection"],
            "es_requirements": ["Threat warning"],
            "spectrum_requirements": ["Basic frequency allocation"],
        }
