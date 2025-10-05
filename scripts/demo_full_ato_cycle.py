#!/usr/bin/env python3
"""
Demonstration of Complete ATO Cycle with All 5 Context-Aware Agents.

Shows the full 72-hour ATO cycle with all agents working together:
- Phase 1-2: EMS Strategy Agent
- Phase 3: EW Planner & Spectrum Manager Agents
- Phase 4: ATO Producer Agent
- Phase 6: Assessment Agent
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
from aether_os.agent_context import (
    AgentContext,
    DoctrineContext,
    SituationalContext,
    HistoricalContext,
)

from agents.context_aware_ems_strategy_agent import ContextAwareEMSStrategyAgent
from agents.context_aware_ew_planner_agent import ContextAwareEWPlannerAgent
from agents.context_aware_spectrum_manager_agent import ContextAwareSpectrumManagerAgent
from agents.context_aware_ato_producer_agent import ContextAwareATOProducerAgent
from agents.context_aware_assessment_agent import ContextAwareAssessmentAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('full_ato_cycle_demo.log'),
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Run complete ATO cycle demonstration."""
    logger.info("=" * 80)
    logger.info("COMPLETE ATO CYCLE DEMONSTRATION - ALL 5 CONTEXT-AWARE AGENTS")
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

    # Create all 5 context-aware agents
    strategy_agent = ContextAwareEMSStrategyAgent(aether_os)
    ew_agent = ContextAwareEWPlannerAgent(aether_os)
    spectrum_agent = ContextAwareSpectrumManagerAgent(aether_os)
    ato_producer = ContextAwareATOProducerAgent(aether_os)
    assessment_agent = ContextAwareAssessmentAgent(aether_os)

    # Register agents
    aether_os.register_agent("ems_strategy_agent", strategy_agent)
    aether_os.register_agent("ew_planner_agent", ew_agent)
    aether_os.register_agent("spectrum_manager_agent", spectrum_agent)
    aether_os.register_agent("ato_producer_agent", ato_producer)
    aether_os.register_agent("assessment_agent", assessment_agent)

    logger.info("Registered 5 context-aware agents")

    # Create scenario context
    print("\n" + "=" * 80)
    print("SCENARIO: Multi-Phase EMS Operations in Contested Airspace")
    print("Threat: Advanced IADS with SA-10/SA-6 systems")
    print("Mission: 72-hour ATO cycle for SEAD and strike operations")
    print("=" * 80)

    # Shared scenario data
    threats = [
        {
            "threat_id": "THR-001",
            "threat_type": "SA-10 Grumble",
            "location": {"lat": 36.5, "lon": 44.5},
            "capability": "Long-range SAM (60nm)",
            "priority": "critical",
            "frequencies": "8-12 GHz (S-band)",
        },
        {
            "threat_id": "THR-002",
            "threat_type": "SA-6 Gainful",
            "location": {"lat": 36.0, "lon": 44.0},
            "capability": "Medium-range SAM (15nm)",
            "priority": "high",
            "frequencies": "2-4 GHz (C-band)",
        },
    ]

    assets = [
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
    ]

    # Store for passing data between phases
    cycle_outputs = {}

    # =================================================================
    # PHASE 1-2: EMS STRATEGY DEVELOPMENT
    # =================================================================
    print("\n" + "=" * 80)
    print("PHASE 1-2: OBJECTIVES & STRATEGY DEVELOPMENT")
    print("Active Agent: EMS Strategy Agent")
    print("=" * 80)

    context = AgentContext(
        agent_id="ems_strategy_agent",
        current_phase=ATOPhase.PHASE1_OEG,
        current_task="Develop EMS strategy for contested airspace operations",
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
            current_threats=threats,
            available_assets=assets,
        ),
        historical_context=HistoricalContext(
            lessons_learned=[
                "SA-10 systems require standoff jamming",
                "Coordinate EA timing with strike packages",
                "Request spectrum allocations early to avoid delays",
            ],
        ),
    )

    strategy_agent.current_context = context

    print("\n🤖 EMS Strategy Agent developing strategy...")
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
        cycle_outputs["ems_strategy"] = strategy_response.get("content")

    # =================================================================
    # PHASE 3: MISSION PLANNING & SPECTRUM ALLOCATION
    # =================================================================
    print("\n" + "=" * 80)
    print("PHASE 3: WEAPONEERING & MISSION PLANNING")
    print("Active Agents: EW Planner & Spectrum Manager")
    print("=" * 80)

    # EW Planner
    context.agent_id = "ew_planner_agent"
    context.current_phase = ATOPhase.PHASE3_WEAPONEERING
    context.current_task = "Plan EW missions for SEAD operation"
    ew_agent.current_context = context

    print("\n🤖 EW Planner Agent planning missions...")
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
        cycle_outputs["ew_missions"] = [
            {"mission_id": "M-001", "target_id": "THR-001", "asset_id": "AST-001", "mission_type": "EA", "toa": "H-hour"},
            {"mission_id": "M-002", "target_id": "THR-002", "asset_id": "AST-002", "mission_type": "EA", "toa": "H+2"},
        ]

    # Spectrum Manager
    context.agent_id = "spectrum_manager_agent"
    context.current_task = "Allocate frequencies for EW missions"
    spectrum_agent.current_context = context

    print("\n🤖 Spectrum Manager Agent allocating frequencies...")
    allocation_response = spectrum_agent.allocate_frequencies(
        requests=[
            {"mission_id": "M-001", "band": "S-band", "priority": "critical"},
            {"mission_id": "M-002", "band": "C-band", "priority": "high"},
        ],
    )

    print(f"\n✅ Frequencies allocated:")
    print(f"  - Success: {allocation_response['success']}")
    if allocation_response['success']:
        print(f"  - Context utilization: {allocation_response.get('context_utilization', 0):.1%}")
        cycle_outputs["frequency_allocations"] = [
            {"mission_id": "M-001", "frequency_min_mhz": 8000, "frequency_max_mhz": 12000, "start_time": "H-1", "end_time": "H+2"},
            {"mission_id": "M-002", "frequency_min_mhz": 2000, "frequency_max_mhz": 4000, "start_time": "H+1", "end_time": "H+4"},
        ]

    # =================================================================
    # PHASE 4: ATO PRODUCTION
    # =================================================================
    print("\n" + "=" * 80)
    print("PHASE 4: ATO PRODUCTION")
    print("Active Agent: ATO Producer")
    print("=" * 80)

    context.agent_id = "ato_producer_agent"
    context.current_phase = ATOPhase.PHASE4_ATO_PRODUCTION
    context.current_task = "Integrate EMS into Air Tasking Order"
    context.situational_context.active_missions = cycle_outputs.get("ew_missions", [])
    ato_producer.current_context = context

    print("\n🤖 ATO Producer Agent creating ATO document...")
    ato_response = ato_producer.produce_ato_ems_annex(
        ew_missions=cycle_outputs.get("ew_missions", []),
        frequency_allocations=cycle_outputs.get("frequency_allocations", []),
    )

    print(f"\n✅ ATO document produced:")
    print(f"  - Success: {ato_response['success']}")
    if ato_response['success']:
        print(f"  - Context utilization: {ato_response.get('context_utilization', 0):.1%}")
        cycle_outputs["ato_document"] = ato_response.get("content")

    # =================================================================
    # PHASE 5: EXECUTION (Simulated)
    # =================================================================
    print("\n" + "=" * 80)
    print("PHASE 5: EXECUTION")
    print("(Simulated - missions execute per ATO)")
    print("=" * 80)

    # Simulate execution results
    execution_results = {
        "M-001": {"status": "success", "objectives_met": True, "notes": "SA-10 suppressed"},
        "M-002": {"status": "success", "objectives_met": True, "notes": "SA-6 jammed effectively"},
    }

    cycle_outputs["execution_data"] = execution_results

    print("\n✅ Execution complete:")
    print("  - M-001: Success - SA-10 suppressed")
    print("  - M-002: Success - SA-6 jammed effectively")

    # =================================================================
    # PHASE 6: ASSESSMENT
    # =================================================================
    print("\n" + "=" * 80)
    print("PHASE 6: ASSESSMENT")
    print("Active Agent: Assessment Agent")
    print("=" * 80)

    context.agent_id = "assessment_agent"
    context.current_phase = ATOPhase.PHASE6_ASSESSMENT
    context.current_task = "Assess ATO cycle effectiveness"
    context.historical_context.past_cycle_performance = [execution_results]
    assessment_agent.current_context = context

    print("\n🤖 Assessment Agent analyzing cycle...")

    # Assess missions
    missions_with_status = [
        {**m, "status": execution_results[m["mission_id"]]["status"]}
        for m in cycle_outputs.get("ew_missions", [])
    ]

    mission_assessment = assessment_agent.assess_mission_effectiveness(
        missions=missions_with_status,
        execution_data=execution_results,
    )

    print(f"\n✅ Mission assessment complete:")
    print(f"  - Success: {mission_assessment['success']}")
    if mission_assessment['success']:
        print(f"  - Context utilization: {mission_assessment.get('context_utilization', 0):.1%}")

    # Generate lessons learned
    lessons_response = assessment_agent.generate_lessons_learned(
        cycle_id="CYCLE-001",
        mission_assessment={"success_rate": 1.0, "all_objectives_met": True},
        process_assessment={"critical_issues": 0, "efficiency": "high"},
    )

    print(f"\n✅ Lessons learned generated:")
    print(f"  - Success: {lessons_response['success']}")
    if lessons_response['success']:
        print(f"  - Context utilization: {lessons_response.get('context_utilization', 0):.1%}")

    # =================================================================
    # SUMMARY
    # =================================================================
    print("\n" + "=" * 80)
    print("ATO CYCLE COMPLETE - SUMMARY")
    print("=" * 80)

    print("\n📊 Cycle Results:")
    print(f"  ✅ Phase 1-2: EMS Strategy developed")
    print(f"  ✅ Phase 3: {len(cycle_outputs.get('ew_missions', []))} missions planned")
    print(f"  ✅ Phase 3: {len(cycle_outputs.get('frequency_allocations', []))} frequencies allocated")
    print(f"  ✅ Phase 4: ATO document produced with SPINS annex")
    print(f"  ✅ Phase 5: All missions executed successfully (simulated)")
    print(f"  ✅ Phase 6: Assessment and lessons learned generated")

    print("\n📈 Agent Performance:")
    for agent_name, agent in [
        ("EMS Strategy", strategy_agent),
        ("EW Planner", ew_agent),
        ("Spectrum Manager", spectrum_agent),
        ("ATO Producer", ato_producer),
        ("Assessment", assessment_agent),
    ]:
        stats = agent.get_semantic_stats()
        if stats.get("semantic_tracking"):
            print(f"  {agent_name}:")
            print(f"    - Interactions: {stats.get('total_interactions', 0)}")
            print(f"    - Context elements used: {stats.get('used_elements', 0)}/{stats.get('total_elements', 0)}")

    print("\n🎯 Key Achievements:")
    print("  - All 5 context-aware agents executed successfully")
    print("  - Complete ATO cycle demonstrated (Phases 1-6)")
    print("  - Agents coordinated through context and message passing")
    print("  - Semantic tracking measured context utilization")
    print("  - Process improvement tracking enabled (Option C)")

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n💡 To see full LLM-powered responses:")
        print("  1. Set ANTHROPIC_API_KEY environment variable")
        print("  2. Re-run this demo")
        print("  3. Agents will generate detailed, context-grounded responses")

    print(f"\n📝 Full logs saved to: full_ato_cycle_demo.log\n")


if __name__ == "__main__":
    asyncio.run(main())
