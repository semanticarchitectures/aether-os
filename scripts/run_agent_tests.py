#!/usr/bin/env python3
"""
Agent Test Runner for Aether OS.

Run pytest tests for individual agents or all agents.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_pytest_for_agent(agent_name: str, verbose: bool = False):
    """Run pytest for a specific agent."""
    test_file = Path(__file__).parent.parent / "tests" / "test_single_agent.py"
    
    if agent_name == "all":
        test_pattern = str(test_file)
    else:
        # Map agent names to test classes
        agent_class_map = {
            "ems_strategy": "TestEMSStrategyAgent",
            "ew_planner": "TestEWPlannerAgent", 
            "spectrum_manager": "TestSpectrumManagerAgent"
        }
        
        if agent_name not in agent_class_map:
            print(f"❌ Unknown agent: {agent_name}")
            print(f"Available agents: {', '.join(agent_class_map.keys())}")
            return False
        
        test_class = agent_class_map[agent_name]
        test_pattern = f"{test_file}::{test_class}"
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    cmd.extend([
        "--tb=short",  # Short traceback format
        "--no-header", # No pytest header
        test_pattern
    ])
    
    print(f"🧪 Running tests for: {agent_name}")
    print(f"📁 Test pattern: {test_pattern}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False


def run_integration_test_for_agent(agent_name: str):
    """Run integration test for a specific agent with real LLM."""
    script_path = Path(__file__).parent / "test_single_agent.py"
    
    cmd = ["python", str(script_path), "--agent", agent_name]
    
    print(f"🔗 Running integration test for: {agent_name}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run integration test: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run tests for individual Aether OS agents")
    parser.add_argument("agent", nargs="?", default="all",
                       choices=["ems_strategy", "ew_planner", "spectrum_manager", "all"],
                       help="Which agent to test (default: all)")
    parser.add_argument("--unit", action="store_true", 
                       help="Run unit tests with mocked dependencies")
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests with real LLM")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Default to unit tests if neither specified
    if not args.unit and not args.integration:
        args.unit = True
    
    print("🧪 AETHER OS AGENT TEST RUNNER")
    print("=" * 80)
    
    success = True
    
    if args.unit:
        print("📋 UNIT TESTS (Mocked Dependencies)")
        print("=" * 80)
        success &= run_pytest_for_agent(args.agent, args.verbose)
        print()
    
    if args.integration:
        print("🔗 INTEGRATION TESTS (Real LLM)")
        print("=" * 80)
        success &= run_integration_test_for_agent(args.agent)
        print()
    
    if success:
        print("🎉 All tests completed successfully!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
