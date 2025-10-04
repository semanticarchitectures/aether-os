"""
Spectrum Manager Agent for Aether OS.

Manages frequency allocation and deconfliction during Phase 3 (Weaponeering)
and Phase 5 (Execution).
"""

from typing import Dict, Any, List, Tuple, Optional
import logging
from datetime import datetime

from agents.base_agent import BaseAetherAgent
from aether_os.access_control import InformationCategory
from aether_os.process_improvement import InefficencyType

logger = logging.getLogger(__name__)


class SpectrumManagerAgent(BaseAetherAgent):
    """
    Spectrum Manager Agent.

    Active Phases: Phase 3 (Weaponeering), Phase 5 (Execution)
    Role: Manages frequency allocation and deconfliction
    Access Level: OPERATIONAL
    """

    def __init__(self, aether_os: Any):
        """Initialize Spectrum Manager Agent."""
        super().__init__(agent_id="spectrum_manager_agent", aether_os=aether_os)

        # Track frequency allocations
        self.pending_requests: List[Dict[str, Any]] = []

    async def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """Execute tasks for the current phase."""
        if phase == "PHASE3_WEAPONEERING":
            return await self._execute_phase3(cycle_id)
        elif phase == "PHASE5_EXECUTION":
            return await self._execute_phase5(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase: {phase}")
            return {}

    async def _execute_phase3(self, cycle_id: str) -> Dict[str, Any]:
        """
        Execute Phase 3 (Weaponeering) tasks.

        Process frequency allocation requests from EW Planner.
        """
        logger.info(f"[{self.agent_id}] Executing Phase 3 (Weaponeering) for cycle {cycle_id}")

        outputs = {}

        # Process pending frequency requests
        if self.pending_requests:
            allocations = self.execute_doctrinal_procedure(
                procedure_name="Process Frequency Allocation Requests",
                procedure_fn=self._process_allocation_requests,
                expected_time_hours=2.0,
                cycle_id=cycle_id,
                phase="PHASE3_WEAPONEERING",
            )
            outputs["frequency_allocations"] = allocations

            # Record output
            self.aether_os.orchestrator.record_output("frequency_allocations", allocations)

        return outputs

    async def _execute_phase5(self, cycle_id: str) -> Dict[str, Any]:
        """
        Execute Phase 5 (Execution) tasks.

        Monitor spectrum usage and handle emergency reallocations.
        """
        logger.info(f"[{self.agent_id}] Executing Phase 5 (Execution) for cycle {cycle_id}")

        outputs = {}

        # In production, would monitor real-time spectrum usage
        # For prototype, placeholder
        outputs["execution_monitoring"] = {
            "status": "monitoring",
            "conflicts_detected": 0,
            "reallocations_performed": 0,
        }

        return outputs

    def process_frequency_request(
        self,
        mission_id: str,
        frequency_range: Tuple[float, float],
        time_window: Tuple[str, str],
        geographic_area: Dict[str, Any],
        priority: str = "normal",
        cycle_id: str = None,
        phase: str = None,
    ) -> Dict[str, Any]:
        """
        Process a frequency allocation request.

        Args:
            mission_id: Mission identifier
            frequency_range: (min_mhz, max_mhz)
            time_window: (start_time, end_time)
            geographic_area: GeoJSON area
            priority: Request priority
            cycle_id: ATO cycle ID
            phase: Current phase

        Returns:
            Allocation result
        """
        logger.info(
            f"[{self.agent_id}] Processing frequency request for mission {mission_id}: "
            f"{frequency_range[0]}-{frequency_range[1]} MHz"
        )

        # Authorize action
        authorized = self.aether_os.authorize_action(
            agent_id=self.agent_id,
            action="allocate_frequency",
            context={
                "frequency_range": frequency_range,
                "time_window": time_window,
                "geographic_area": geographic_area,
            },
        )

        if not authorized:
            logger.error("Frequency allocation not authorized")
            return {
                "success": False,
                "error": "Authorization denied",
            }

        # Check for conflicts
        conflicts = self._check_spectrum_conflicts(
            frequency_range, time_window, geographic_area
        )

        if conflicts:
            logger.warning(f"Frequency conflicts detected: {len(conflicts)} conflicts")

            # Coordinate deconfliction per doctrine
            deconfliction_result = self.execute_doctrinal_procedure(
                procedure_name="Coordinate Spectrum Deconfliction",
                procedure_fn=self.coordinate_deconfliction,
                expected_time_hours=1.0,
                cycle_id=cycle_id or "UNKNOWN",
                phase=phase or "PHASE3_WEAPONEERING",
                conflicts=conflicts,
                requested_range=frequency_range,
            )

            if not deconfliction_result["resolved"]:
                return {
                    "success": False,
                    "error": "Deconfliction failed",
                    "conflicts": conflicts,
                }

        # Create allocation
        allocation = {
            "allocation_id": f"ALLOC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "mission_id": mission_id,
            "frequency_min_mhz": frequency_range[0],
            "frequency_max_mhz": frequency_range[1],
            "start_time": time_window[0],
            "end_time": time_window[1],
            "geographic_area": geographic_area,
            "priority": priority,
            "status": "allocated",
        }

        logger.info(f"Frequency allocated: {allocation['allocation_id']}")

        return {
            "success": True,
            "allocation": allocation,
        }

    def _check_spectrum_conflicts(
        self,
        frequency_range: Tuple[float, float],
        time_window: Tuple[str, str],
        geographic_area: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Check for spectrum conflicts.

        In production, would call spectrum MCP server.
        """
        # Placeholder - would query spectrum database via MCP
        # For now, return no conflicts

        conflicts = []

        # Simulate occasional conflict for testing
        import random
        if random.random() < 0.2:  # 20% chance of conflict
            conflicts.append({
                "conflict_type": "frequency_overlap",
                "conflicting_allocation": "ALLOC-EXISTING-001",
                "overlap_mhz": 50.0,
            })

        return conflicts

    def coordinate_deconfliction(
        self,
        conflicts: List[Dict[str, Any]],
        requested_range: Tuple[float, float],
    ) -> Dict[str, Any]:
        """
        Coordinate spectrum deconfliction per JCEOI process.

        This follows doctrine but may flag inefficiencies.
        """
        logger.info(f"[{self.agent_id}] Coordinating deconfliction for {len(conflicts)} conflicts")

        coordination_start = datetime.now()

        # Per doctrine, coordinate with each conflicting user
        for i, conflict in enumerate(conflicts):
            logger.info(f"Coordinating with conflicting allocation: {conflict.get('conflicting_allocation')}")

            # Simulate coordination delay
            import time
            time.sleep(0.5)  # Simulate coordination time

        coordination_time_hours = (datetime.now() - coordination_start).total_seconds() / 3600

        # Flag if coordination was excessive
        if len(conflicts) > 2:
            self.flag_redundant_coordination(
                workflow_name="Coordinate Spectrum Deconfliction",
                coordination_description=f"Coordinated with {len(conflicts)} conflicting users individually",
                time_wasted_hours=coordination_time_hours * 0.5,  # Estimate 50% could be automated
                cycle_id=self.aether_os.get_current_cycle_id() or "UNKNOWN",
                phase="PHASE3_WEAPONEERING",
            )

        # For prototype, assume deconfliction succeeds
        return {
            "resolved": True,
            "method": "manual_coordination",
            "coordination_time_hours": coordination_time_hours,
        }

    def emergency_reallocation(
        self,
        allocation_id: str,
        reason: str,
        new_frequency_range: Optional[Tuple[float, float]] = None,
    ) -> Dict[str, Any]:
        """
        Perform emergency frequency reallocation during execution.

        Requires senior approval per doctrine.
        """
        logger.warning(
            f"[{self.agent_id}] Emergency reallocation requested: "
            f"allocation={allocation_id}, reason={reason}"
        )

        # Escalate to human for approval
        human_decision = self.escalate_for_human_decision(
            decision_type="emergency_spectrum_reallocation",
            context={
                "allocation_id": allocation_id,
                "reason": reason,
                "new_frequency_range": new_frequency_range,
            },
            reason="Emergency reallocation requires O-5+ approval per doctrine",
        )

        if not human_decision.get("approved"):
            return {
                "success": False,
                "error": "Emergency reallocation not approved",
            }

        # Perform reallocation
        logger.info(f"Emergency reallocation approved by {human_decision.get('human_operator')}")

        return {
            "success": True,
            "new_allocation_id": f"ALLOC-EMERGENCY-{datetime.now().strftime('%H%M%S')}",
            "approved_by": human_decision.get("human_operator"),
        }

    def _process_allocation_requests(self, cycle_id: str) -> List[Dict[str, Any]]:
        """Process all pending frequency allocation requests."""
        logger.info(f"Processing {len(self.pending_requests)} frequency requests")

        allocations = []

        for request in self.pending_requests:
            result = self.process_frequency_request(
                mission_id=request["mission_id"],
                frequency_range=request["frequency_range"],
                time_window=request["time_window"],
                geographic_area=request["geographic_area"],
                priority=request.get("priority", "normal"),
                cycle_id=cycle_id,
                phase="PHASE3_WEAPONEERING",
            )

            if result["success"]:
                allocations.append(result["allocation"])

        # Clear pending requests
        self.pending_requests = []

        return allocations

    def _handle_frequency_request(
        self,
        from_agent: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle frequency request message from another agent."""
        logger.info(f"[{self.agent_id}] Received frequency request from {from_agent}")

        # Add to pending requests
        self.pending_requests.append(payload)

        return {
            "success": True,
            "message": "Frequency request queued for processing",
            "queue_position": len(self.pending_requests),
        }
