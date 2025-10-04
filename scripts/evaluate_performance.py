#!/usr/bin/env python3
"""
Agent Performance Evaluation Script.

Evaluates agent performance across multiple ATO cycles and generates
comprehensive reports including context utilization and optimization recommendations.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aether_os.core import AetherOS
from aether_os.orchestrator import ATOPhase
from agents.ems_strategy_agent import EMSStrategyAgent
from agents.spectrum_manager_agent import SpectrumManagerAgent
from agents.ew_planner_agent import EWPlannerAgent
from agents.ato_producer_agent import ATOProducerAgent
from agents.assessment_agent import AssessmentAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('performance_evaluation.log'),
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run performance evaluation."""

    logger.info("=" * 80)
    logger.info("AETHER OS - AGENT PERFORMANCE EVALUATION")
    logger.info("=" * 80)

    # Initialize Aether OS
    doctrine_kb_path = "doctrine_kb/chroma_db"
    opa_url = os.getenv("OPA_URL", "http://localhost:8181")

    aether_os = AetherOS(
        doctrine_kb_path=doctrine_kb_path,
        opa_url=opa_url,
    )

    logger.info("Aether OS initialized")

    # Create and register all agents
    agents = [
        EMSStrategyAgent(aether_os),
        SpectrumManagerAgent(aether_os),
        EWPlannerAgent(aether_os),
        ATOProducerAgent(aether_os),
        AssessmentAgent(aether_os),
    ]

    for agent in agents:
        aether_os.register_agent(agent.agent_id, agent)

    logger.info(f"Registered {len(agents)} agents")

    # Start ATO cycle
    cycle_id = aether_os.start_ato_cycle()
    logger.info(f"Started ATO cycle: {cycle_id}")

    # Simulate cycle execution through all phases
    logger.info("\n" + "=" * 80)
    logger.info("SIMULATING ATO CYCLE EXECUTION")
    logger.info("=" * 80)

    # Execute each phase
    phases = [
        (ATOPhase.PHASE1_OEG, ["ems_strategy_agent"]),
        (ATOPhase.PHASE2_TARGET_DEVELOPMENT, ["ems_strategy_agent"]),
        (ATOPhase.PHASE3_WEAPONEERING, ["ew_planner_agent", "spectrum_manager_agent"]),
        (ATOPhase.PHASE4_ATO_PRODUCTION, ["ato_producer_agent"]),
        (ATOPhase.PHASE5_EXECUTION, ["spectrum_manager_agent"]),
        (ATOPhase.PHASE6_ASSESSMENT, ["assessment_agent"]),
    ]

    import asyncio

    async def execute_phases():
        """Execute all phases."""
        for phase_enum, active_agent_ids in phases:
            logger.info(f"\n--- {phase_enum.value} ---")

            # Transition to phase
            aether_os.orchestrator.current_cycle.current_phase = phase_enum

            # Execute tasks for active agents
            for agent_id in active_agent_ids:
                agent = next((a for a in agents if a.agent_id == agent_id), None)
                if agent:
                    try:
                        # Activate agent
                        await aether_os.activate_agent(agent_id)

                        # Execute phase tasks (this will use context)
                        result = await agent.execute_phase_tasks(phase_enum.value, cycle_id)

                        logger.info(f"  {agent_id}: Completed tasks")

                    except Exception as e:
                        logger.error(f"  {agent_id}: Error - {e}", exc_info=True)

    asyncio.run(execute_phases())

    # Evaluate agent performance
    logger.info("\n" + "=" * 80)
    logger.info("AGENT PERFORMANCE EVALUATION")
    logger.info("=" * 80)

    for agent in agents:
        logger.info(f"\nEvaluating {agent.agent_id}...")

        try:
            # Evaluate performance
            metrics = aether_os.evaluate_agent_performance(
                agent_id=agent.agent_id,
                cycle_id=cycle_id,
            )

            # Generate report
            report = aether_os.get_performance_report(
                agent_id=agent.agent_id,
                cycles=1,
            )

            print(report)

        except Exception as e:
            logger.error(f"Error evaluating {agent.agent_id}: {e}", exc_info=True)

    # Context optimization analysis
    logger.info("\n" + "=" * 80)
    logger.info("CONTEXT OPTIMIZATION ANALYSIS")
    logger.info("=" * 80)

    try:
        # Get optimization report
        optimization_report = aether_os.get_context_optimization_report()
        print("\n" + optimization_report)

        # Get context-performance correlation analysis
        correlation_analysis = aether_os.get_context_performance_analysis()

        print("\nCONTEXT-PERFORMANCE CORRELATION")
        print("-" * 60)

        if correlation_analysis.get("high_performers"):
            print("\nHigh Performers:")
            for perf in correlation_analysis["high_performers"]:
                print(f"  {perf['agent_id']}: Score {perf['overall_score']:.2f}, "
                      f"Context Util: {perf['context_utilization']:.1%}")

        if correlation_analysis.get("low_performers"):
            print("\nLow Performers:")
            for perf in correlation_analysis["low_performers"]:
                print(f"  {perf['agent_id']}: Score {perf['overall_score']:.2f}, "
                      f"Context Util: {perf['context_utilization']:.1%}")

        if correlation_analysis.get("recommendations"):
            print("\nRecommendations:")
            for rec in correlation_analysis["recommendations"]:
                print(f"  - {rec}")

    except Exception as e:
        logger.error(f"Error in optimization analysis: {e}", exc_info=True)

    # Context statistics
    logger.info("\n" + "=" * 80)
    logger.info("CONTEXT USAGE STATISTICS")
    logger.info("=" * 80)

    for agent in agents:
        stats = aether_os.context_manager.get_context_statistics(agent.agent_id)

        if stats:
            print(f"\n{agent.agent_id}:")
            print(f"  Contexts Provided: {stats.get('total_contexts_provided', 0)}")
            print(f"  Avg Utilization: {stats.get('avg_utilization_rate', 0):.1%}")
            print(f"  Avg Size: {stats.get('avg_context_size', 0):.0f} tokens")

    # Comparative analysis
    logger.info("\n" + "=" * 80)
    logger.info("COMPARATIVE AGENT ANALYSIS")
    logger.info("=" * 80)

    comparative = aether_os.performance_evaluator.get_comparative_analysis()

    if comparative:
        print("\n{:<25} {:>12} {:>12} {:>12} {:>12}".format(
            "Agent", "Overall", "Mission", "Efficiency", "Collaboration"
        ))
        print("-" * 73)

        for agent_id, metrics in comparative.items():
            print("{:<25} {:>12.2f} {:>12.1%} {:>12.1%} {:>12.2f}".format(
                agent_id,
                metrics['overall_score'],
                metrics['mission_success'],
                metrics['efficiency'],
                metrics['collaboration'],
            ))

    # Process improvement summary
    logger.info("\n" + "=" * 80)
    logger.info("PROCESS IMPROVEMENT SUMMARY")
    logger.info("=" * 80)

    improvement_report = aether_os.get_process_improvement_report()
    print(improvement_report)

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("EVALUATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Evaluated {len(agents)} agents across 1 ATO cycle")
    logger.info("Reports saved to: performance_evaluation.log")


if __name__ == "__main__":
    main()
