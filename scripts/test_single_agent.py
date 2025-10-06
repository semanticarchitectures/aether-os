#!/usr/bin/env python3
"""
Single Agent Testing Script for Aether OS.

Run unit tests for individual agents without requiring the full system.
"""

import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aether_os.llm_client import LLMClient
from aether_os.context_processor import ContextProcessor
from aether_os.semantic_context_tracker import SemanticContextTracker
from aether_os.agent_context import AgentContext, DoctrineContext, SituationalContext
from aether_os.orchestrator import ATOPhase
from agents.context_aware_ems_strategy_agent import ContextAwareEMSStrategyAgent
from agents.context_aware_ew_planner_agent import ContextAwareEWPlannerAgent
from agents.context_aware_spectrum_manager_agent import ContextAwareSpectrumManagerAgent


def create_test_context():
    """Create a sample context for testing."""
    doctrine = DoctrineContext(
        relevant_procedures=[
            {
                "id": "DOC-PROC-001",
                "content": "Develop EMS strategy aligned with air component objectives",
                "source": "JP 3-13.1"
            },
            {
                "id": "DOC-PROC-002",
                "content": "Consider EA, EP, and ES operations holistically",
                "source": "AFI 10-703"
            }
        ],
        best_practices=[
            "Integrate EMS effects early in planning",
            "Coordinate spectrum requirements with all users"
        ]
    )

    situational = SituationalContext(
        current_threats=[
            {
                "id": "THR-001",
                "type": "SA-10 Grumble",
                "location": [36.5, 44.5],
                "capability": "Long-range SAM (60nm)",
                "priority": "critical"
            },
            {
                "id": "THR-002",
                "type": "SA-6 Gainful",
                "location": [36.0, 44.0],
                "capability": "Medium-range SAM (15nm)",
                "priority": "high"
            }
        ],
        available_assets=[
            {
                "id": "AST-001",
                "type": "EA-18G Growler",
                "capability": "Stand-in jamming",
                "status": "available"
            },
            {
                "id": "AST-002",
                "type": "EC-130H Compass Call",
                "capability": "Communications jamming",
                "status": "available"
            }
        ],
        spectrum_status={
            "existing_allocations": [
                {
                    "mission": "ISR-001",
                    "freq_mhz": "3000-4000",
                    "time": "H-2 to H+6"
                }
            ]
        }
    )

    return AgentContext(
        agent_id="test_agent",
        current_phase=ATOPhase.PHASE1_OEG,
        doctrinal_context=doctrine,
        situational_context=situational,
        historical_context=None,
        collaborative_context=None
    )


def test_ems_strategy_agent():
    """Test EMS Strategy Agent with real LLM."""
    print("=" * 80)
    print("TESTING EMS STRATEGY AGENT")
    print("=" * 80)
    
    # Create agent
    agent = ContextAwareEMSStrategyAgent("test_ems_strategy")
    
    # Create test context
    context = create_test_context()
    
    print("🤖 Testing strategy development...")
    
    try:
        result = agent.develop_strategy(
            mission_objectives=["Neutralize enemy air defenses", "Enable strike operations"],
            commanders_guidance="Prioritize force protection while achieving mission objectives",
            timeline="Execute during ATO Phase 1-2 (6-14 hours)"
        )
        
        print("✅ Strategy development successful!")
        print(f"📊 Result type: {type(result)}")
        
        if hasattr(result, 'strategy_summary'):
            print(f"📋 Strategy: {result.strategy_summary[:100]}...")
            print(f"🎯 Objectives: {len(result.objectives)} objectives")
            print(f"📚 Citations: {len(result.context_citations)} context citations")
            print(f"🔍 Confidence: {result.confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy development failed: {e}")
        return False


def test_ew_planner_agent():
    """Test EW Planner Agent with real LLM."""
    print("=" * 80)
    print("TESTING EW PLANNER AGENT")
    print("=" * 80)
    
    # Create agent
    agent = ContextAwareEWPlannerAgent("test_ew_planner")
    
    # Create test context
    context = create_test_context()
    
    print("🤖 Testing mission planning...")
    
    try:
        result = agent.plan_missions(
            mission_type="SEAD (Suppression of Enemy Air Defenses)",
            targets=["THR-001", "THR-002"],
            timeframe="H to H+4 hours",
            context=context
        )
        
        print("✅ Mission planning successful!")
        print(f"📊 Result type: {type(result)}")
        
        if hasattr(result, 'missions'):
            print(f"🎯 Missions: {len(result.missions)} missions planned")
            print(f"📡 Frequency requests: {len(result.frequency_requests)} requests")
            print(f"📚 Citations: {len(result.context_citations)} context citations")
            print(f"🔍 Confidence: {result.confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mission planning failed: {e}")
        return False


def test_spectrum_manager_agent():
    """Test Spectrum Manager Agent with real LLM."""
    print("=" * 80)
    print("TESTING SPECTRUM MANAGER AGENT")
    print("=" * 80)
    
    # Create agent
    agent = ContextAwareSpectrumManagerAgent("test_spectrum_manager")
    
    # Create test context
    context = create_test_context()
    
    print("🤖 Testing frequency allocation...")
    
    try:
        result = agent.allocate_frequencies(
            requests=[
                "S-band jamming frequencies for SA-10 engagement (3.0-3.5 GHz)",
                "VHF/UHF communications jamming for SA-6 command links (30-400 MHz)"
            ],
            context=context
        )
        
        print("✅ Frequency allocation successful!")
        print(f"📊 Result type: {type(result)}")
        
        if hasattr(result, 'allocations'):
            print(f"📡 Allocations: {len(result.allocations)} frequency allocations")
            print(f"⚠️  Conflicts: {len(result.conflicts_identified)} conflicts identified")
            print(f"🔧 Deconflictions: {len(result.deconfliction_actions)} actions taken")
            print(f"📚 Citations: {len(result.context_citations)} context citations")
            print(f"🔍 Confidence: {result.confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Frequency allocation failed: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test individual Aether OS agents")
    parser.add_argument("--agent", choices=["ems_strategy", "ew_planner", "spectrum_manager", "all"],
                       default="all", help="Which agent to test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("🧪 AETHER OS SINGLE AGENT TESTING")
    print("=" * 80)
    
    results = {}
    
    if args.agent in ["ems_strategy", "all"]:
        results["ems_strategy"] = test_ems_strategy_agent()
        print()
    
    if args.agent in ["ew_planner", "all"]:
        results["ew_planner"] = test_ew_planner_agent()
        print()
    
    if args.agent in ["spectrum_manager", "all"]:
        results["spectrum_manager"] = test_spectrum_manager_agent()
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for agent, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{agent.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
