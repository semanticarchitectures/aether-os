#!/usr/bin/env python3
"""
Examine LLM Interaction Logs for Aether OS.

This script provides tools to analyze and examine the detailed LLM
prompts and responses logged by the system.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aether_os.llm_interaction_logger import get_llm_logger


def print_interaction_stats():
    """Print statistics about logged interactions."""
    logger = get_llm_logger()
    stats = logger.get_interaction_stats()
    
    print("=" * 80)
    print("LLM INTERACTION STATISTICS")
    print("=" * 80)
    print(f"Total interactions: {stats['total_interactions']}")
    print(f"Successful: {stats['successful_interactions']}")
    print(f"Failed: {stats['failed_interactions']}")
    print(f"Total tokens used: {stats['total_tokens']:,}")
    
    if stats['total_interactions'] > 0:
        success_rate = stats['successful_interactions'] / stats['total_interactions'] * 100
        avg_tokens = stats['total_tokens'] / stats['total_interactions']
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Average tokens per interaction: {avg_tokens:.1f}")
    
    print("\nBy Provider:")
    for provider, count in stats.get('providers', {}).items():
        print(f"  {provider}: {count} interactions")
    
    print("\nBy Agent:")
    for agent, count in stats.get('agents', {}).items():
        print(f"  {agent}: {count} interactions")
    
    print("\nBy Model:")
    for model, count in stats.get('models', {}).items():
        print(f"  {model}: {count} interactions")


def show_recent_interactions(limit: int = 5):
    """Show recent interactions."""
    logger = get_llm_logger()
    interactions = logger.search_interactions(limit=limit)
    
    print("=" * 80)
    print(f"RECENT INTERACTIONS (Last {len(interactions)})")
    print("=" * 80)
    
    for i, interaction in enumerate(interactions, 1):
        timestamp = interaction['timestamp']
        agent_id = interaction['agent_id']
        provider = interaction['provider']
        model = interaction['model']
        tokens = interaction['tokens_used']
        success = "✅" if interaction['success'] else "❌"
        
        print(f"\n{i}. [{timestamp}] {success}")
        print(f"   Agent: {agent_id}")
        print(f"   Provider: {provider} ({model})")
        print(f"   Tokens: {tokens}")
        
        if interaction.get('error'):
            print(f"   Error: {interaction['error']}")


def show_interaction_details(interaction_index: int):
    """Show detailed view of a specific interaction."""
    logger = get_llm_logger()
    interactions = logger.search_interactions(limit=100)
    
    if interaction_index < 1 or interaction_index > len(interactions):
        print(f"Invalid interaction index. Available: 1-{len(interactions)}")
        return
    
    interaction = interactions[interaction_index - 1]
    
    print("=" * 80)
    print(f"INTERACTION DETAILS #{interaction_index}")
    print("=" * 80)
    print(f"Timestamp: {interaction['timestamp']}")
    print(f"Agent: {interaction['agent_id']}")
    print(f"Provider: {interaction['provider']}")
    print(f"Model: {interaction['model']}")
    print(f"Tokens: {interaction['tokens_used']}")
    print(f"Success: {'Yes' if interaction['success'] else 'No'}")
    
    if interaction.get('error'):
        print(f"Error: {interaction['error']}")
    
    print("\n" + "-" * 40)
    print("SYSTEM PROMPT:")
    print("-" * 40)
    system_prompt = interaction.get('system_prompt', '')
    if system_prompt:
        print(system_prompt[:1000] + ("..." if len(system_prompt) > 1000 else ""))
    else:
        print("(No system prompt)")
    
    print("\n" + "-" * 40)
    print("USER PROMPT:")
    print("-" * 40)
    user_prompt = interaction.get('user_prompt', '')
    print(user_prompt[:1000] + ("..." if len(user_prompt) > 1000 else ""))
    
    if interaction['success'] and interaction.get('response_content'):
        print("\n" + "-" * 40)
        print("RESPONSE:")
        print("-" * 40)
        response = interaction['response_content']
        print(response[:1000] + ("..." if len(response) > 1000 else ""))


def search_interactions_by_agent(agent_id: str, limit: int = 10):
    """Search interactions by agent ID."""
    logger = get_llm_logger()
    interactions = logger.search_interactions(agent_id=agent_id, limit=limit)
    
    print("=" * 80)
    print(f"INTERACTIONS FOR AGENT: {agent_id}")
    print("=" * 80)
    
    if not interactions:
        print("No interactions found for this agent.")
        return
    
    for i, interaction in enumerate(interactions, 1):
        timestamp = interaction['timestamp']
        provider = interaction['provider']
        tokens = interaction['tokens_used']
        success = "✅" if interaction['success'] else "❌"
        
        print(f"{i}. [{timestamp}] {success} {provider} - {tokens} tokens")


def search_interactions_by_provider(provider: str, limit: int = 10):
    """Search interactions by provider."""
    logger = get_llm_logger()
    interactions = logger.search_interactions(provider=provider, limit=limit)
    
    print("=" * 80)
    print(f"INTERACTIONS FOR PROVIDER: {provider}")
    print("=" * 80)
    
    if not interactions:
        print("No interactions found for this provider.")
        return
    
    for i, interaction in enumerate(interactions, 1):
        timestamp = interaction['timestamp']
        agent_id = interaction['agent_id']
        tokens = interaction['tokens_used']
        success = "✅" if interaction['success'] else "❌"
        
        print(f"{i}. [{timestamp}] {success} {agent_id} - {tokens} tokens")


def show_log_files():
    """Show information about log files."""
    logger = get_llm_logger()
    
    print("=" * 80)
    print("LLM LOG FILES")
    print("=" * 80)
    
    text_log = logger.text_log_path
    json_log = logger.json_log_path
    
    print(f"Text log: {text_log}")
    if text_log.exists():
        size = text_log.stat().st_size
        print(f"  Size: {size:,} bytes")
        print(f"  Modified: {datetime.fromtimestamp(text_log.stat().st_mtime)}")
    else:
        print("  Status: Does not exist")
    
    print(f"\nJSON log: {json_log}")
    if json_log.exists():
        size = json_log.stat().st_size
        lines = sum(1 for _ in open(json_log))
        print(f"  Size: {size:,} bytes")
        print(f"  Lines: {lines:,}")
        print(f"  Modified: {datetime.fromtimestamp(json_log.stat().st_mtime)}")
    else:
        print("  Status: Does not exist")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Examine LLM interaction logs")
    parser.add_argument("--stats", action="store_true", help="Show interaction statistics")
    parser.add_argument("--recent", type=int, default=5, help="Show recent interactions")
    parser.add_argument("--details", type=int, help="Show details for interaction number")
    parser.add_argument("--agent", type=str, help="Search by agent ID")
    parser.add_argument("--provider", type=str, help="Search by provider")
    parser.add_argument("--files", action="store_true", help="Show log file information")
    parser.add_argument("--limit", type=int, default=10, help="Limit results")
    
    args = parser.parse_args()
    
    if args.stats:
        print_interaction_stats()
    elif args.details:
        show_interaction_details(args.details)
    elif args.agent:
        search_interactions_by_agent(args.agent, args.limit)
    elif args.provider:
        search_interactions_by_provider(args.provider, args.limit)
    elif args.files:
        show_log_files()
    else:
        # Default: show recent interactions
        show_recent_interactions(args.recent)


if __name__ == "__main__":
    main()
