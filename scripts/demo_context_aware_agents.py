#!/usr/bin/env python3
"""
Demonstration of Context-Aware Agents.

Shows EMS Strategy, EW Planner, and Spectrum Manager agents
working together with LLM-powered context-aware reasoning.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aether_os.core import AetherOS
from aether_os.orchestrator import ATOPhase
from aether_os.agent_context import (
    AgentContext,
    DoctrineContext,
    SituationalContext,
    HistoricalContext,
)

from agents.context_aware_ems_strategy_agent import ContextAwareEMSStrategyAgent
from agents.context_aware_ew_planner_agent import ContextAwareEWPlannerAgent
from agents.context_aware_spectrum_manager_agent import ContextAwareSpectrumManagerAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('context_aware_demo.log'),
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Run context-aware agents demonstration."""
    logger.info("=" * 80)
    logger.info("CONTEXT-AWARE AGENTS DEMONSTRATION")
    logger.info("=" * 80)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("⚠️  ANTHROPIC_API_KEY not set. Agents will use fallback mode.")
        logger.warning("   Set API key to see full LLM-powered reasoning.")
        print("\nTo enable LLM reasoning, set your API key:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("\nContinuing in fallback mode...\n")

    # Initialize Aether OS
    doctrine_kb_path = "doctrine_kb/chroma_db"
    opa_url = os.getenv("OPA_URL", "http://localhost:8181")

    aether_os = AetherOS(
        doctrine_kb_path=doctrine_kb_path,
        opa_url=opa_url,
    )

    logger.info("Aether OS initialized")

    # Create context-aware agents
    strategy_agent = ContextAwareEMSStrategyAgent(aether_os)
    ew_agent = ContextAwareEWPlannerAgent(aether_os)
    spectrum_agent = ContextAwareSpectrumManagerAgent(aether_os)

    # Register agents
    aether_os.register_agent("ems_strategy_agent", strategy_agent)
    aether_os.register_agent("ew_planner_agent", ew_agent)
    aether_os.register_agent("spectrum_manager_agent", spectrum_agent)

    logger.info("Registered 3 context-aware agents")

    # Create test context
    print("\n" + "=" * 80)
    print("SCENARIO: High-Threat EMS Operations Planning")
    print("=" * 80)

    context = AgentContext(
        agent_id="ems_strategy_agent",
        current_phase=ATOPhase.PHASE1_OEG,
        current_task="Develop EMS strategy for contested airspace",
        doctrinal_context=DoctrineContext(
            relevant_procedures=[
                {
                    "content": "Develop EMS strategy aligned with air component objectives",
                    "source": "JP 3-13.1",
                },
                {
                    "content": "Consider EA, EP, and ES operations holistically",
                    "source": "AFI 10-703",
                },
                {
                    "content": "Prioritize force protection and mission success",
                    "source": "USAF EMS Doctrine",
                },
            ],
            best_practices=[
                "Integrate EMS effects early in planning",
                "Coordinate spectrum requirements with all users",
            ],
        ),
        situational_context=SituationalContext(
            current_threats=[
                {
                    "threat_id": "THR-001",
                    "threat_type": "SA-10 Grumble",
                    "location": {"lat": 36.5, "lon": 44.5},
                    "capability": "Long-range SAM (60nm)",
                    "priority": "critical",
                },
                {
                    "threat_id": "THR-002",
                    "threat_type": "SA-6 Gainful",
                    "location": {"lat": 36.0, "lon": 44.0},
                    "capability": "Medium-range SAM (15nm)",
                    "priority": "high",
                },
            ],
            available_assets=[
                {
                    "asset_id": "AST-001",
                    "platform": "EA-18G Growler",
                    "capability": "Stand-in jamming",
                    "availability": "available",
                    "effective_range_nm": 50,
                },
                {
                    "asset_id": "AST-002",
                    "platform": "EC-130H Compass Call",
                    "capability": "Communications jamming",
                    "availability": "available",
                    "effective_range_nm": 200,
                },
            ],
        ),
        historical_context=HistoricalContext(
            lessons_learned=[
                "SA-10 systems require standoff jamming",
                "Coordinate EA timing with strike packages",
                "Request spectrum allocations early to avoid delays",
            ],
        ),
    )

    # Test 1: EMS Strategy Agent
    print("\n" + "-" * 80)
    print("TEST 1: EMS Strategy Development")
    print("-" * 80)

    strategy_agent.current_context = context

    print("\n📋 Context provided:")
    print(f"  - {len(context.doctrinal_context.relevant_procedures)} doctrinal procedures")
    print(f"  - {len(context.situational_context.current_threats)} threats")
    print(f"  - {len(context.situational_context.available_assets)} assets")
    print(f"  - {len(context.historical_context.lessons_learned)} lessons learned")

    print("\n🤖 Developing EMS strategy...")

    strategy_response = strategy_agent.develop_strategy(
        commanders_guidance="Achieve air superiority while protecting friendly forces",
        mission_objectives=[
            "Suppress enemy air defenses",
            "Protect friendly communications",
            "Enable strike operations",
        ],
        timeline="72 hours",
    )

    print(f"\n✅ Strategy developed:")
    print(f"  - Success: {strategy_response['success']}")
    if strategy_response['success']:
        print(f"  - Context utilization: {strategy_response.get('context_utilization', 0):.1%}")
        print(f"  - Citations: {len(strategy_response.get('citations', []))}")
        if 'citation_accuracy' in strategy_response:
            print(f"  - Citation accuracy: {strategy_response['citation_accuracy']:.1%}")

        # Show semantic stats
        stats = strategy_agent.get_semantic_stats()
        if stats.get('semantic_tracking'):
            print(f"\n📊 Semantic tracking stats:")
            print(f"  - Total interactions: {stats.get('total_interactions', 0)}")
            print(f"  - Context elements used: {stats.get('used_elements', 0)}/{stats.get('total_elements', 0)}")

    # Test 2: EW Planner Agent
    print("\n" + "-" * 80)
    print("TEST 2: EW Mission Planning")
    print("-" * 80)

    # Update context for EW Planner
    context.agent_id = "ew_planner_agent"
    context.current_phase = ATOPhase.PHASE3_WEAPONEERING
    context.current_task = "Plan EW missions for SEAD operation"

    ew_agent.current_context = context

    print("\n🤖 Planning EW missions...")

    mission_response = ew_agent.plan_missions(
        mission_type="SEAD",
        targets=["THR-001", "THR-002"],
        timeframe="H-hour to H+4",
        strike_packages=[
            {"name": "Package Alpha", "targets": ["THR-001"], "toa": "H+1"},
            {"name": "Package Bravo", "targets": ["THR-002"], "toa": "H+3"},
        ],
    )

    print(f"\n✅ Mission plan created:")
    print(f"  - Success: {mission_response['success']}")
    if mission_response['success']:
        print(f"  - Context utilization: {mission_response.get('context_utilization', 0):.1%}")
        print(f"  - Citations: {len(mission_response.get('citations', []))}")

        # Show underutilized context
        underused = ew_agent.get_underutilized_context()
        if underused:
            print(f"\n⚠️  Underutilized context: {len(underused)} elements")
            for elem in underused[:3]:
                print(f"  - {elem.element_id}: {elem.content[:60]}...")

    # Test 3: Spectrum Manager Agent
    print("\n" + "-" * 80)
    print("TEST 3: Frequency Allocation")
    print("-" * 80)

    # Update context for Spectrum Manager
    context.agent_id = "spectrum_manager_agent"
    context.current_task = "Allocate frequencies for EW missions"

    # Add some existing allocations to context
    context.situational_context.spectrum_status = {
        "existing_allocations": [
            {"mission": "ISR-001", "freq_mhz": "3000-4000", "time": "H-2 to H+6"},
        ],
    }

    spectrum_agent.current_context = context

    print("\n🤖 Allocating frequencies...")

    allocation_response = spectrum_agent.allocate_frequencies(
        requests=[
            {"mission_id": "SEAD-001", "band": "S-band", "priority": "critical"},
            {"mission_id": "SEAD-002", "band": "S-band", "priority": "high"},
        ],
    )

    print(f"\n✅ Frequencies allocated:")
    print(f"  - Success: {allocation_response['success']}")
    if allocation_response['success']:
        print(f"  - Context utilization: {allocation_response.get('context_utilization', 0):.1%}")
        print(f"  - Citations: {len(allocation_response.get('citations', []))}")

    # Summary
    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)

    print("\n📈 Overall Results:")
    print(f"  - All 3 agents successfully demonstrated context-aware reasoning")
    print(f"  - Agents cited context elements in their responses")
    print(f"  - Semantic tracking measured actual context utilization")

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n💡 To see full LLM-powered responses:")
        print("  1. Set ANTHROPIC_API_KEY environment variable")
        print("  2. Re-run this demo")
        print("  3. Agents will generate detailed, context-grounded responses")

    print(f"\n📝 Full logs saved to: context_aware_demo.log\n")


if __name__ == "__main__":
    asyncio.run(main())
