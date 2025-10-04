#!/usr/bin/env python3
"""
Run test scenarios from YAML files.
"""

import os
import sys
import logging
import asyncio
import yaml
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
from agents.ato_producer_agent import ATOProducerAgent
from agents.assessment_agent import AssessmentAgent
from agents.evaluator_agent import EvaluatorAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('yaml_scenario_test.log'),
    ]
)

logger = logging.getLogger(__name__)


def load_yaml_scenario(yaml_path: str) -> AgentTestScenario:
    """Load test scenario from YAML file."""
    logger.info(f"Loading scenario from: {yaml_path}")

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    # Parse context
    context_data = data.get('context', {})

    # Convert phase string to enum
    phase_str = context_data.get('phase', 'PHASE1_OEG')
    phase = getattr(ATOPhase, phase_str)

    context = TestContext(
        phase=phase,
        task_description=context_data.get('task_description', ''),
        threats=context_data.get('threats', []),
        assets=context_data.get('assets', []),
        missions=context_data.get('missions', []),
        doctrinal_procedures=context_data.get('doctrinal_procedures', []),
        historical_lessons=context_data.get('historical_lessons', []),
        max_context_size=context_data.get('max_context_size', 32000),
    )

    # Parse messages
    messages = [
        TestMessage(
            message_type=msg.get('message_type'),
            payload=msg.get('payload', {}),
            description=msg.get('description', ''),
        )
        for msg in data.get('messages', [])
    ]

    # Create scenario
    scenario = AgentTestScenario(
        scenario_id=data.get('scenario_id'),
        name=data.get('name'),
        description=data.get('description'),
        agent_id=data.get('agent_id'),
        context=context,
        messages=messages,
        evaluation_criteria=data.get('evaluation_criteria', {}),
        tags=data.get('tags', []),
        difficulty=data.get('difficulty', 'medium'),
    )

    logger.info(f"Loaded scenario: {scenario.name}")
    return scenario


async def main():
    """Run YAML scenario."""
    if len(sys.argv) < 2:
        print("Usage: python run_yaml_scenario.py <path_to_yaml>")
        print("\nExample:")
        print("  python scripts/run_yaml_scenario.py scenarios/agent_tests/example_ew_planner.yaml")
        sys.exit(1)

    yaml_path = sys.argv[1]

    if not os.path.exists(yaml_path):
        print(f"Error: File not found: {yaml_path}")
        sys.exit(1)

    logger.info("=" * 80)
    logger.info("AETHER OS - YAML SCENARIO TEST")
    logger.info("=" * 80)

    # Load scenario
    scenario = load_yaml_scenario(yaml_path)

    # Initialize Aether OS
    doctrine_kb_path = "doctrine_kb/chroma_db"
    opa_url = os.getenv("OPA_URL", "http://localhost:8181")

    aether_os = AetherOS(
        doctrine_kb_path=doctrine_kb_path,
        opa_url=opa_url,
    )

    logger.info("Aether OS initialized")

    # Create all agents
    agents = {
        "ems_strategy_agent": EMSStrategyAgent(aether_os),
        "ew_planner_agent": EWPlannerAgent(aether_os),
        "spectrum_manager_agent": SpectrumManagerAgent(aether_os),
        "ato_producer_agent": ATOProducerAgent(aether_os),
        "assessment_agent": AssessmentAgent(aether_os),
    }

    # Create evaluator
    evaluator = EvaluatorAgent(aether_os)

    # Register agents
    for agent_id, agent in agents.items():
        aether_os.register_agent(agent_id, agent)

    logger.info(f"Registered {len(agents)} agents")

    # Get the agent to test
    agent = agents.get(scenario.agent_id)
    if not agent:
        print(f"Error: Unknown agent ID: {scenario.agent_id}")
        print(f"Available agents: {list(agents.keys())}")
        sys.exit(1)

    # Create test runner
    test_runner = AgentTestRunner(
        aether_os=aether_os,
        evaluator_agent=evaluator,
    )

    # Run scenario
    logger.info("\n" + "=" * 80)
    logger.info(f"RUNNING SCENARIO: {scenario.name}")
    logger.info("=" * 80)
    logger.info(f"Agent: {scenario.agent_id}")
    logger.info(f"Difficulty: {scenario.difficulty}")
    logger.info(f"Messages: {len(scenario.messages)}")
    logger.info(f"Criteria: {len(scenario.evaluation_criteria)}")
    logger.info("=" * 80 + "\n")

    result = await test_runner.run_scenario(scenario, agent)

    # Display results
    print("\n" + "=" * 80)
    print(f"TEST RESULT: {scenario.name}")
    print("=" * 80)
    print(f"Scenario ID: {result.scenario_id}")
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
        print("Evaluation Feedback:")
        print(result.evaluation_feedback)
        print()

    if result.response_log:
        print("Response Log:")
        for idx, response in enumerate(result.response_log, 1):
            print(f"\n  Message {idx}: {response.get('message_type')}")
            print(f"  Response: {response.get('response')}")
        print()

    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
        print()

    print("=" * 80)
    logger.info(f"Test complete. Logs saved to: yaml_scenario_test.log")


if __name__ == "__main__":
    asyncio.run(main())
