"""
ATO Cycle Orchestrator for Aether OS.

Manages the 72-hour Air Tasking Order cycle, activating/deactivating agents
based on phase timing and orchestrating agent coordination.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)


class ATOPhase(Enum):
    """ATO cycle phases."""
    PHASE1_OEG = "PHASE1_OEG"                            # Objectives, Effects, Guidance
    PHASE2_TARGET_DEVELOPMENT = "PHASE2_TARGET_DEVELOPMENT"
    PHASE3_WEAPONEERING = "PHASE3_WEAPONEERING"
    PHASE4_ATO_PRODUCTION = "PHASE4_ATO_PRODUCTION"
    PHASE5_EXECUTION = "PHASE5_EXECUTION"
    PHASE6_ASSESSMENT = "PHASE6_ASSESSMENT"


@dataclass
class PhaseDefinition:
    """Definition of an ATO phase."""
    phase: ATOPhase
    duration_hours: float
    offset_hours: float
    active_agents: List[str]
    key_outputs: List[str]
    critical: bool = False


@dataclass
class ATOCycle:
    """Represents a single ATO cycle."""
    cycle_id: str
    start_time: datetime
    end_time: datetime
    current_phase: Optional[ATOPhase] = None
    phase_history: List[tuple[ATOPhase, datetime]] = field(default_factory=list)
    outputs: Dict[str, any] = field(default_factory=dict)
    status: str = "active"  # active, completed, cancelled


class ATOCycleOrchestrator:
    """
    Orchestrates the 72-hour ATO cycle.

    Acts as a "process scheduler" that activates agents based on phase timing,
    manages phase transitions, and coordinates agent activities.
    """

    def __init__(self):
        """Initialize the ATO cycle orchestrator."""
        self.phase_definitions = self._define_phase_schedule()
        self.current_cycle: Optional[ATOCycle] = None
        self.cycle_history: List[ATOCycle] = []
        self._cycle_counter = 0
        self._monitoring_task: Optional[asyncio.Task] = None
        self._phase_callbacks: Dict[ATOPhase, List[Callable]] = {}
        logger.info("ATOCycleOrchestrator initialized")

    def _define_phase_schedule(self) -> Dict[ATOPhase, PhaseDefinition]:
        """
        Define the ATO phase schedule.

        Total cycle: 72 hours
        """
        return {
            ATOPhase.PHASE1_OEG: PhaseDefinition(
                phase=ATOPhase.PHASE1_OEG,
                duration_hours=6,
                offset_hours=0,
                active_agents=["ems_strategy_agent"],
                key_outputs=["ems_strategy", "commander_guidance"],
                critical=False,
            ),
            ATOPhase.PHASE2_TARGET_DEVELOPMENT: PhaseDefinition(
                phase=ATOPhase.PHASE2_TARGET_DEVELOPMENT,
                duration_hours=8,
                offset_hours=6,
                active_agents=["ems_strategy_agent"],
                key_outputs=["target_list", "ems_requirements"],
                critical=False,
            ),
            ATOPhase.PHASE3_WEAPONEERING: PhaseDefinition(
                phase=ATOPhase.PHASE3_WEAPONEERING,
                duration_hours=10,
                offset_hours=14,
                active_agents=["ew_planner_agent", "spectrum_manager_agent"],
                key_outputs=["ew_missions", "frequency_allocations"],
                critical=True,
            ),
            ATOPhase.PHASE4_ATO_PRODUCTION: PhaseDefinition(
                phase=ATOPhase.PHASE4_ATO_PRODUCTION,
                duration_hours=6,
                offset_hours=24,
                active_agents=["ato_producer_agent", "spectrum_manager_agent"],
                key_outputs=["ato_document", "spins_annex"],
                critical=True,
            ),
            ATOPhase.PHASE5_EXECUTION: PhaseDefinition(
                phase=ATOPhase.PHASE5_EXECUTION,
                duration_hours=24,
                offset_hours=30,
                active_agents=["spectrum_manager_agent"],
                key_outputs=["execution_data", "real_time_adjustments"],
                critical=False,
            ),
            ATOPhase.PHASE6_ASSESSMENT: PhaseDefinition(
                phase=ATOPhase.PHASE6_ASSESSMENT,
                duration_hours=18,
                offset_hours=54,
                active_agents=["assessment_agent"],
                key_outputs=["effectiveness_assessment", "lessons_learned"],
                critical=False,
            ),
        }

    def start_new_cycle(self, start_time: Optional[datetime] = None) -> ATOCycle:
        """
        Start a new ATO cycle.

        Args:
            start_time: Cycle start time (defaults to now)

        Returns:
            The created ATOCycle
        """
        if self.current_cycle and self.current_cycle.status == "active":
            logger.warning(f"Ending current cycle {self.current_cycle.cycle_id} to start new one")
            self.current_cycle.status = "cancelled"
            self.cycle_history.append(self.current_cycle)

        self._cycle_counter += 1
        cycle_start = start_time or datetime.now()

        self.current_cycle = ATOCycle(
            cycle_id=f"ATO-{self._cycle_counter:04d}",
            start_time=cycle_start,
            end_time=cycle_start + timedelta(hours=72),
            status="active",
        )

        logger.info(
            f"Started new ATO cycle: {self.current_cycle.cycle_id} "
            f"(Start: {cycle_start}, End: {self.current_cycle.end_time})"
        )

        # Start with Phase 1
        self._transition_to_phase(ATOPhase.PHASE1_OEG)

        return self.current_cycle

    def get_current_phase(self) -> Optional[ATOPhase]:
        """Get the current ATO phase."""
        if not self.current_cycle:
            return None
        return self.current_cycle.current_phase

    def get_active_agents(self) -> List[str]:
        """Get list of agents that should be active in current phase."""
        current_phase = self.get_current_phase()
        if not current_phase:
            return []

        phase_def = self.phase_definitions.get(current_phase)
        return phase_def.active_agents if phase_def else []

    def is_agent_active(self, agent_id: str) -> bool:
        """Check if a specific agent should be active in current phase."""
        return agent_id in self.get_active_agents()

    def get_phase_at_time(self, check_time: datetime) -> Optional[ATOPhase]:
        """
        Determine which phase should be active at a given time.

        Args:
            check_time: Time to check

        Returns:
            The phase that should be active, or None if outside cycle
        """
        if not self.current_cycle:
            return None

        # Check if time is within cycle
        if check_time < self.current_cycle.start_time or check_time >= self.current_cycle.end_time:
            return None

        # Calculate hours since cycle start
        hours_elapsed = (check_time - self.current_cycle.start_time).total_seconds() / 3600

        # Find the appropriate phase
        for phase, phase_def in self.phase_definitions.items():
            phase_start = phase_def.offset_hours
            phase_end = phase_def.offset_hours + phase_def.duration_hours

            if phase_start <= hours_elapsed < phase_end:
                return phase

        return None

    def _transition_to_phase(self, new_phase: ATOPhase) -> None:
        """
        Transition to a new phase.

        Args:
            new_phase: The phase to transition to
        """
        if not self.current_cycle:
            logger.error("Cannot transition phase: no active cycle")
            return

        old_phase = self.current_cycle.current_phase
        transition_time = datetime.now()

        self.current_cycle.current_phase = new_phase
        self.current_cycle.phase_history.append((new_phase, transition_time))

        phase_def = self.phase_definitions[new_phase]

        logger.info(
            f"Phase transition: {old_phase.value if old_phase else 'None'} -> {new_phase.value} "
            f"| Cycle: {self.current_cycle.cycle_id} "
            f"| Active agents: {', '.join(phase_def.active_agents)}"
        )

        # Execute phase callbacks
        self._execute_phase_callbacks(new_phase)

    def _execute_phase_callbacks(self, phase: ATOPhase) -> None:
        """Execute registered callbacks for phase transition."""
        callbacks = self._phase_callbacks.get(phase, [])
        for callback in callbacks:
            try:
                callback(phase, self.current_cycle)
            except Exception as e:
                logger.error(f"Error executing phase callback: {e}", exc_info=True)

    def register_phase_callback(self, phase: ATOPhase, callback: Callable) -> None:
        """
        Register a callback to be executed when entering a phase.

        Args:
            phase: The phase to register for
            callback: Callback function (receives phase and cycle as arguments)
        """
        if phase not in self._phase_callbacks:
            self._phase_callbacks[phase] = []
        self._phase_callbacks[phase].append(callback)
        logger.debug(f"Registered callback for phase {phase.value}")

    async def start_monitoring(self) -> None:
        """Start background monitoring task for phase transitions."""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("Monitoring task already running")
            return

        self._monitoring_task = asyncio.create_task(self._monitor_cycle())
        logger.info("Started ATO cycle monitoring task")

    async def stop_monitoring(self) -> None:
        """Stop background monitoring task."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped ATO cycle monitoring task")

    async def _monitor_cycle(self) -> None:
        """
        Background task to monitor cycle and trigger phase transitions.

        Checks every minute to see if phase transition is needed.
        """
        logger.info("ATO cycle monitoring started")

        try:
            while True:
                if self.current_cycle and self.current_cycle.status == "active":
                    current_time = datetime.now()

                    # Check if cycle is complete
                    if current_time >= self.current_cycle.end_time:
                        logger.info(f"ATO cycle {self.current_cycle.cycle_id} completed")
                        self.current_cycle.status = "completed"
                        self.cycle_history.append(self.current_cycle)
                        self.current_cycle = None
                    else:
                        # Check if phase transition is needed
                        expected_phase = self.get_phase_at_time(current_time)
                        if expected_phase and expected_phase != self.current_cycle.current_phase:
                            self._transition_to_phase(expected_phase)

                # Sleep for 1 minute before next check
                await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info("ATO cycle monitoring cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in cycle monitoring: {e}", exc_info=True)

    def record_output(self, output_name: str, output_value: any) -> None:
        """
        Record an output for the current cycle.

        Args:
            output_name: Name of the output
            output_value: The output value
        """
        if not self.current_cycle:
            logger.error("Cannot record output: no active cycle")
            return

        self.current_cycle.outputs[output_name] = output_value
        logger.info(f"Recorded output '{output_name}' for cycle {self.current_cycle.cycle_id}")

    def get_cycle_summary(self, cycle_id: Optional[str] = None) -> Dict:
        """
        Get summary of a cycle.

        Args:
            cycle_id: Cycle ID (None for current cycle)

        Returns:
            Dictionary with cycle summary
        """
        if cycle_id:
            cycle = next((c for c in self.cycle_history if c.cycle_id == cycle_id), None)
        else:
            cycle = self.current_cycle

        if not cycle:
            return {}

        return {
            "cycle_id": cycle.cycle_id,
            "start_time": cycle.start_time.isoformat(),
            "end_time": cycle.end_time.isoformat(),
            "current_phase": cycle.current_phase.value if cycle.current_phase else None,
            "status": cycle.status,
            "phase_history": [
                {"phase": phase.value, "time": time.isoformat()}
                for phase, time in cycle.phase_history
            ],
            "outputs": list(cycle.outputs.keys()),
        }
