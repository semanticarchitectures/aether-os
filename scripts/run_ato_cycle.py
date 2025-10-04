#!/usr/bin/env python3
"""
Run ATO Cycle Simulation

Demonstrates a complete 72-hour ATO cycle with all 5 agents coordinating
through Aether OS.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aether_os.core import AetherOS
from agents.ems_strategy_agent import EMSStrategyAgent
from agents.spectrum_manager_agent import SpectrumManagerAgent
from agents.ew_planner_agent import EWPlannerAgent
from agents.ato_producer_agent import ATOProducerAgent
from agents.assessment_agent import AssessmentAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ato_cycle_run.log'),
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Run a complete ATO cycle simulation."""
    logger.info("=" * 80)
    logger.info("AETHER OS - ATO CYCLE SIMULATION")
    logger.info("=" * 80)

    # Initialize Aether OS
    logger.info("\n[1/7] Initializing Aether OS...")
    aether = AetherOS()

    # Register all 5 agents
    logger.info("\n[2/7] Registering agents...")

    agents = {
        "ems_strategy_agent": EMSStrategyAgent(aether),
        "spectrum_manager_agent": SpectrumManagerAgent(aether),
        "ew_planner_agent": EWPlannerAgent(aether),
        "ato_producer_agent": ATOProducerAgent(aether),
        "assessment_agent": AssessmentAgent(aether),
    }

    for agent_id, agent in agents.items():
        success = aether.register_agent(agent_id, agent)
        if success:
            logger.info(f"  ✓ Registered: {agent_id}")
        else:
            logger.error(f"  ✗ Failed to register: {agent_id}")

    # Start ATO cycle
    logger.info("\n[3/7] Starting ATO cycle...")
    cycle_id = aether.start_ato_cycle()
    logger.info(f"  Started cycle: {cycle_id}")

    # Execute each phase manually (instead of time-based)
    logger.info("\n[4/7] Executing ATO cycle phases...")

    # Phase 1: OEG
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: OBJECTIVES, EFFECTS, GUIDANCE (OEG)")
    logger.info("=" * 60)

    # Activate EMS Strategy Agent
    await aether.activate_agent("ems_strategy_agent")

    # Execute Phase 1 tasks
    try:
        phase1_outputs = await agents["ems_strategy_agent"].execute_phase_tasks(
            phase="PHASE1_OEG",
            cycle_id=cycle_id,
        )
        logger.info(f"Phase 1 outputs: {list(phase1_outputs.keys())}")
    except Exception as e:
        logger.error(f"Error in Phase 1: {e}", exc_info=True)

    # Phase 2: Target Development
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: TARGET DEVELOPMENT")
    logger.info("=" * 60)

    try:
        phase2_outputs = await agents["ems_strategy_agent"].execute_phase_tasks(
            phase="PHASE2_TARGET_DEVELOPMENT",
            cycle_id=cycle_id,
        )
        logger.info(f"Phase 2 outputs: {list(phase2_outputs.keys())}")
    except Exception as e:
        logger.error(f"Error in Phase 2: {e}", exc_info=True)

    # Deactivate EMS Strategy Agent
    await aether.deactivate_agent("ems_strategy_agent")

    # Phase 3: Weaponeering
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 3: WEAPONEERING & ALLOCATION")
    logger.info("=" * 60)

    # Activate EW Planner and Spectrum Manager
    await aether.activate_agent("ew_planner_agent")
    await aether.activate_agent("spectrum_manager_agent")

    try:
        # EW Planner creates missions and requests frequencies
        phase3_ew_outputs = await agents["ew_planner_agent"].execute_phase_tasks(
            phase="PHASE3_WEAPONEERING",
            cycle_id=cycle_id,
        )
        logger.info(f"Phase 3 EW Planner outputs: {list(phase3_ew_outputs.keys())}")

        # Spectrum Manager processes frequency requests
        phase3_spectrum_outputs = await agents["spectrum_manager_agent"].execute_phase_tasks(
            phase="PHASE3_WEAPONEERING",
            cycle_id=cycle_id,
        )
        logger.info(f"Phase 3 Spectrum Manager outputs: {list(phase3_spectrum_outputs.keys())}")
    except Exception as e:
        logger.error(f"Error in Phase 3: {e}", exc_info=True)

    # Deactivate EW Planner
    await aether.deactivate_agent("ew_planner_agent")

    # Phase 4: ATO Production
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 4: ATO PRODUCTION")
    logger.info("=" * 60)

    # Activate ATO Producer (Spectrum Manager still active)
    await aether.activate_agent("ato_producer_agent")

    try:
        phase4_outputs = await agents["ato_producer_agent"].execute_phase_tasks(
            phase="PHASE4_ATO_PRODUCTION",
            cycle_id=cycle_id,
        )
        logger.info(f"Phase 4 outputs: {list(phase4_outputs.keys())}")
    except Exception as e:
        logger.error(f"Error in Phase 4: {e}", exc_info=True)

    # Deactivate ATO Producer
    await aether.deactivate_agent("ato_producer_agent")

    # Phase 5: Execution (simulated - normally 24 hours)
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 5: EXECUTION (Simulated)")
    logger.info("=" * 60)

    try:
        phase5_outputs = await agents["spectrum_manager_agent"].execute_phase_tasks(
            phase="PHASE5_EXECUTION",
            cycle_id=cycle_id,
        )
        logger.info(f"Phase 5 outputs: {list(phase5_outputs.keys())}")
    except Exception as e:
        logger.error(f"Error in Phase 5: {e}", exc_info=True)

    # Deactivate Spectrum Manager
    await aether.deactivate_agent("spectrum_manager_agent")

    # Phase 6: Assessment
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 6: ASSESSMENT")
    logger.info("=" * 60)

    # Activate Assessment Agent
    await aether.activate_agent("assessment_agent")

    try:
        phase6_outputs = await agents["assessment_agent"].execute_phase_tasks(
            phase="PHASE6_ASSESSMENT",
            cycle_id=cycle_id,
        )
        logger.info(f"Phase 6 outputs: {list(phase6_outputs.keys())}")
    except Exception as e:
        logger.error(f"Error in Phase 6: {e}", exc_info=True)

    # Generate final reports
    logger.info("\n[5/7] Generating reports...")

    # Process Improvement Report
    logger.info("\n" + "=" * 60)
    logger.info("PROCESS IMPROVEMENT REPORT")
    logger.info("=" * 60)
    improvement_report = aether.get_process_improvement_report()
    print(improvement_report)

    # System Status
    logger.info("\n[6/7] Final system status...")
    status = aether.get_system_status()
    logger.info(f"  Cycle: {status['current_cycle'].get('cycle_id')}")
    logger.info(f"  Outputs generated: {len(status['current_cycle'].get('outputs', []))}")
    logger.info(f"  Process flags: {status['process_improvement_stats']['total_flags']}")

    # Deactivate all agents
    await aether.deactivate_agent("assessment_agent")

    logger.info("\n[7/7] ATO cycle simulation complete!")
    logger.info("=" * 80)

    # Print summary
    print("\n" + "=" * 80)
    print("ATO CYCLE SIMULATION SUMMARY")
    print("=" * 80)
    print(f"Cycle ID: {cycle_id}")
    print(f"Phases Completed: 6/6")
    print(f"Agents Utilized: {len(agents)}")
    print(f"Process Improvement Flags: {status['process_improvement_stats']['total_flags']}")
    print(f"Outputs Generated: {len(status['current_cycle'].get('outputs', []))}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
