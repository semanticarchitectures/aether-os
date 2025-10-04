#!/usr/bin/env python3
"""
Agent Testing Script.

Test individual agents with custom contexts and messages,
and evaluate their responses using the EvaluatorAgent.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aether_os.core import AetherOS
from aether_os.orchestrator import ATOPhase
from aether_os.agent_testing import (
    AgentTestScenario,
    TestContext,
    TestMessage,
    AgentTestRunner,
)

from agents.ems_strategy_agent import EMSStrategyAgent
from agents.ew_planner_agent import EWPlannerAgent
from agents.spectrum_manager_agent import SpectrumManagerAgent
from agents.evaluator_agent import EvaluatorAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_testing.log'),
    ]
)

logger = logging.getLogger(__name__)


def create_example_scenarios() -> list:
    """Create example test scenarios."""
    scenarios = []

    # Scenario 1: EMS Strategy Development Test
    scenario1 = AgentTestScenario(
        scenario_id="test_ems_strategy_001",
        name="EMS Strategy Development - High Threat",
        description="Test EMS strategy agent's ability to develop strategy in high-threat environment",
        agent_id="ems_strategy_agent",
        context=TestContext(
            phase=ATOPhase.PHASE1_OEG,
            task_description="Develop EMS strategy for contested airspace",
            threats=[
                {
                    "threat_id": "THREAT-001",
                    "threat_type": "IADS",
                    "location": {"lat": 35.0, "lon": 45.0},
                    "capability": "Advanced SAM system",
                    "frequency_range": "2-18 GHz",
                },
                {
                    "threat_id": "THREAT-002",
                    "threat_type": "EW",
                    "location": {"lat": 35.2, "lon": 45.1},
                    "capability": "Jamming system",
                    "frequency_range": "1-6 GHz",
                },
            ],
            doctrinal_procedures=[
                "Develop EMS strategy aligned with air component objectives",
                "Consider EA, EP, and ES operations holistically",
                "Prioritize force protection and mission success",
            ],
            max_context_size=16000,
        ),
        messages=[
            TestMessage(
                message_type="develop_strategy",
                payload={
                    "mission_objectives": [
                        "Achieve air superiority",
                        "Suppress enemy air defenses",
                        "Protect friendly communications",
                    ],
                    "timeline": "72 hours",
                },
                description="Request EMS strategy development",
            ),
        ],
        evaluation_criteria={
            "strategy_completeness": {
                "type": "quality",
                "weight": 0.4,
                "target": 0.8,
                "description": "Strategy includes all required components",
            },
            "threat_consideration": {
                "type": "quality",
                "weight": 0.3,
                "target": 0.7,
                "description": "Strategy addresses identified threats",
            },
            "doctrinal_compliance": {
                "type": "compliance",
                "weight": 0.3,
                "target": 0.9,
                "description": "Strategy follows USAF doctrine",
            },
        },
        tags=["strategy", "high-threat", "phase1"],
        difficulty="medium",
    )
    scenarios.append(scenario1)

    # Scenario 2: EW Mission Planning Test
    scenario2 = AgentTestScenario(
        scenario_id="test_ew_planning_001",
        name="EW Mission Planning - Multi-Target",
        description="Test EW planner's ability to plan missions against multiple targets",
        agent_id="ew_planner_agent",
        context=TestContext(
            phase=ATOPhase.PHASE3_WEAPONEERING,
            task_description="Plan EW missions for SEAD operation",
            threats=[
                {
                    "threat_id": "SAM-001",
                    "threat_type": "SA-6",
                    "location": {"lat": 36.0, "lon": 44.0},
                    "priority": "high",
                },
                {
                    "threat_id": "SAM-002",
                    "threat_type": "SA-10",
                    "location": {"lat": 36.5, "lon": 44.5},
                    "priority": "critical",
                },
            ],
            assets=[
                {
                    "asset_id": "EA-001",
                    "platform": "EA-18G",
                    "capability": "Stand-in jamming",
                    "availability": "available",
                },
                {
                    "asset_id": "EA-002",
                    "platform": "EC-130H",
                    "capability": "Standoff jamming",
                    "availability": "available",
                },
            ],
            doctrinal_procedures=[
                "Assign appropriate assets to missions",
                "Check for EA/SIGINT fratricide",
                "Request frequency allocations early",
            ],
            max_context_size=20000,
        ),
        messages=[
            TestMessage(
                message_type="plan_missions",
                payload={
                    "mission_type": "SEAD",
                    "targets": ["SAM-001", "SAM-002"],
                    "timeframe": "H-hour to H+4",
                },
                description="Request EW mission planning",
            ),
        ],
        evaluation_criteria={
            "mission_completion": {
                "type": "completion",
                "weight": 0.3,
                "target": 1.0,
                "description": "All targets have missions assigned",
            },
            "asset_assignment": {
                "type": "quality",
                "weight": 0.3,
                "target": 0.8,
                "description": "Assets assigned appropriately",
            },
            "context_utilization": {
                "type": "utilization",
                "weight": 0.2,
                "target": 0.6,
                "description": "Effective use of provided context",
            },
            "fratricide_check": {
                "type": "compliance",
                "weight": 0.2,
                "target": 1.0,
                "description": "EA/SIGINT fratricide checked",
            },
        },
        tags=["planning", "ew_missions", "phase3"],
        difficulty="hard",
    )
    scenarios.append(scenario2)

    # Scenario 3: Spectrum Management Test
    scenario3 = AgentTestScenario(
        scenario_id="test_spectrum_001",
        name="Frequency Allocation - Conflict Resolution",
        description="Test spectrum manager's conflict resolution",
        agent_id="spectrum_manager_agent",
        context=TestContext(
            phase=ATOPhase.PHASE3_WEAPONEERING,
            task_description="Allocate frequencies and resolve conflicts",
            missions=[
                {
                    "mission_id": "SEAD-001",
                    "frequency_request": {"min": 2000, "max": 4000, "unit": "MHz"},
                    "priority": "high",
                },
                {
                    "mission_id": "ISR-001",
                    "frequency_request": {"min": 3000, "max": 5000, "unit": "MHz"},
                    "priority": "medium",
                },
            ],
            doctrinal_procedures=[
                "Follow JCEOI process for allocations",
                "Coordinate to deconflict overlapping requests",
                "Prioritize by mission criticality",
            ],
        ),
        messages=[
            TestMessage(
                message_type="allocate_frequencies",
                payload={
                    "requests": [
                        {"mission_id": "SEAD-001", "band": "S-band"},
                        {"mission_id": "ISR-001", "band": "S-band"},
                    ],
                },
                description="Request frequency allocations with potential conflict",
            ),
        ],
        evaluation_criteria={
            "conflict_resolution": {
                "type": "quality",
                "weight": 0.4,
                "target": 0.9,
                "description": "Conflicts identified and resolved",
            },
            "allocation_success": {
                "type": "completion",
                "weight": 0.3,
                "target": 1.0,
                "description": "All missions receive allocations",
            },
            "doctrinal_process": {
                "type": "compliance",
                "weight": 0.3,
                "target": 0.8,
                "description": "Follows JCEOI process",
            },
        },
        tags=["spectrum", "conflict_resolution", "phase3"],
        difficulty="medium",
    )
    scenarios.append(scenario3)

    return scenarios


async def main():
    """Run agent testing."""
    logger.info("=" * 80)
    logger.info("AETHER OS - AGENT TESTING")
    logger.info("=" * 80)

    # Initialize Aether OS
    doctrine_kb_path = "doctrine_kb/chroma_db"
    opa_url = os.getenv("OPA_URL", "http://localhost:8181")

    aether_os = AetherOS(
        doctrine_kb_path=doctrine_kb_path,
        opa_url=opa_url,
    )

    logger.info("Aether OS initialized")

    # Create agents
    agents = {
        "ems_strategy_agent": EMSStrategyAgent(aether_os),
        "ew_planner_agent": EWPlannerAgent(aether_os),
        "spectrum_manager_agent": SpectrumManagerAgent(aether_os),
    }

    # Create evaluator agent
    evaluator = EvaluatorAgent(aether_os)

    # Register agents
    for agent_id, agent in agents.items():
        aether_os.register_agent(agent_id, agent)

    logger.info(f"Registered {len(agents)} agents for testing")

    # Create test runner
    test_runner = AgentTestRunner(
        aether_os=aether_os,
        evaluator_agent=evaluator,
    )

    # Create test scenarios
    scenarios = create_example_scenarios()
    logger.info(f"Created {len(scenarios)} test scenarios")

    # Run tests
    logger.info("\n" + "=" * 80)
    logger.info("RUNNING TEST SCENARIOS")
    logger.info("=" * 80)

    for scenario in scenarios:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Scenario: {scenario.name}")
        logger.info(f"Agent: {scenario.agent_id}")
        logger.info(f"Difficulty: {scenario.difficulty}")
        logger.info(f"{'=' * 80}\n")

        # Get agent
        agent = agents.get(scenario.agent_id)
        if not agent:
            logger.error(f"Agent {scenario.agent_id} not found")
            continue

        # Run test
        result = await test_runner.run_scenario(scenario, agent)

        # Display result
        print(f"\n{'=' * 80}")
        print(f"TEST RESULT: {scenario.name}")
        print(f"{'=' * 80}")
        print(f"Agent: {result.agent_id}")
        print(f"Status: {'PASSED ✓' if result.passed else 'FAILED ✗'}")
        print(f"Overall Score: {result.evaluation_score:.2f}/1.0")
        print(f"Execution Time: {result.execution_time_seconds:.2f}s")
        print(f"Context Utilization: {result.context_utilization:.1%}")
        print()

        if result.criteria_scores:
            print("Criterion Scores:")
            for criterion, score in result.criteria_scores.items():
                print(f"  {criterion}: {score:.2f}")
            print()

        if result.evaluation_feedback:
            print("Feedback:")
            print(result.evaluation_feedback)
            print()

        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")
            print()

    # Generate summary report
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    report = test_runner.generate_test_report()
    print(report)

    logger.info("Testing complete")
    logger.info(f"Full logs saved to: agent_testing.log")


if __name__ == "__main__":
    asyncio.run(main())
