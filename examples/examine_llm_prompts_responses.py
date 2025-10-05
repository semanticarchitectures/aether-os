#!/usr/bin/env python3
"""
LLM Prompts and Responses Examination Tool

This script demonstrates how to access, examine, and analyze LLM prompts
and responses in the Aether OS system.

Usage:
    python examples/examine_llm_prompts_responses.py
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from aether_os.prompt_builder import PromptBuilder, TASK_TEMPLATES
from aether_os.context_processor import ContextProcessor, ProcessedContext
from aether_os.llm_client import LLMClient, LLMProvider
from aether_os.agent_context import AgentContext, DoctrineContext, SituationalContext
from aether_os.orchestrator import ATOPhase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def examine_prompt_templates():
    """Examine available prompt templates."""
    print("=== PROMPT TEMPLATES ===")
    print()
    
    for template_name, template_content in TASK_TEMPLATES.items():
        print(f"📋 Template: {template_name}")
        print(f"Length: {len(template_content)} characters")
        print("Preview:")
        preview = template_content.replace('\n', ' ')[:200] + "..."
        print(f"  {preview}")
        print()


def build_sample_prompts():
    """Build sample prompts to show structure."""
    print("=== SAMPLE PROMPT CONSTRUCTION ===")
    print()
    
    # Initialize prompt builder
    builder = PromptBuilder()
    
    # Sample roles and tasks
    test_cases = [
        {
            "role": "ems_strategy",
            "task": "Develop EMS strategy for A2/AD environment",
            "context_summary": "High-threat environment with S-400, S-300 systems"
        },
        {
            "role": "ew_planner", 
            "task": "Plan SEAD missions against layered air defenses",
            "context_summary": "3 SAM sites, 2 EA-18G available, coordination with strike packages"
        },
        {
            "role": "spectrum_manager",
            "task": "Allocate frequencies for EW missions",
            "context_summary": "5 frequency requests, potential conflicts in X-band"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔧 Test Case {i}: {test_case['role'].upper()}")
        print("-" * 50)
        
        # Build simple prompt
        system_prompt, user_prompt = builder.build_simple_prompt(
            role=test_case["role"],
            task=test_case["task"],
            context_summary=test_case["context_summary"]
        )
        
        print("SYSTEM PROMPT:")
        print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
        print()
        
        print("USER PROMPT:")
        print(user_prompt)
        print()
        print("=" * 60)
        print()


def examine_context_processing():
    """Examine how context is processed for LLM consumption."""
    print("=== CONTEXT PROCESSING EXAMPLE ===")
    print()
    
    # Create sample context
    sample_context = AgentContext(
        agent_id="ew_planner_agent",
        current_phase=ATOPhase.PHASE3_WEAPONEERING,
        current_task="Plan EW missions for high-threat environment",
        doctrinal_context=DoctrineContext(
            relevant_procedures=[
                {
                    "content": "Assign assets based on capability and threat level",
                    "source": "JP 3-13.1",
                    "authority": "Joint",
                    "element_id": "DOC-PROC-001"
                },
                {
                    "content": "Check for EA/SIGINT fratricide before mission execution",
                    "source": "AFI 10-703",
                    "authority": "Service", 
                    "element_id": "DOC-PROC-002"
                }
            ],
            applicable_policies=[
                {
                    "content": "Maintain spectrum discipline during operations",
                    "source": "CJCSI 6212.01",
                    "element_id": "DOC-POL-001"
                }
            ],
            best_practices=[
                "Request frequency allocations 24 hours in advance",
                "Coordinate with coalition partners on shared frequencies"
            ]
        ),
        situational_context=SituationalContext(
            current_threats=[
                {
                    "threat_id": "SAM-001",
                    "threat_type": "S-400",
                    "location": {"lat": 36.0, "lon": 44.0},
                    "priority": "critical",
                    "element_id": "THR-001"
                }
            ],
            available_assets=[
                {
                    "asset_id": "EA-001",
                    "platform": "EA-18G",
                    "capability": "Stand-in jamming",
                    "element_id": "AST-001"
                }
            ]
        )
    )
    
    # Process context
    processor = ContextProcessor()
    processed_context = processor.process(
        context=sample_context,
        task_description="Plan EW missions",
        max_tokens=4000
    )
    
    print(f"📊 Processed Context Stats:")
    print(f"  Total tokens: {processed_context.total_tokens}")
    print(f"  Element IDs: {processed_context.element_ids}")
    print(f"  Truncated: {processed_context.truncated}")
    print()
    
    print("📋 Doctrinal Context:")
    print(processed_context.doctrinal_context[:300] + "..." if len(processed_context.doctrinal_context) > 300 else processed_context.doctrinal_context)
    print()
    
    print("🎯 Situational Context:")
    print(processed_context.situational_context[:300] + "..." if len(processed_context.situational_context) > 300 else processed_context.situational_context)
    print()
    
    return processed_context


def demonstrate_llm_interaction(processed_context: ProcessedContext):
    """Demonstrate LLM interaction with prompts and responses."""
    print("=== LLM INTERACTION DEMONSTRATION ===")
    print()
    
    # Build complete prompt
    builder = PromptBuilder()
    system_prompt, user_prompt = builder.build_prompt(
        role="ew_planner",
        task_description="Plan EW missions for the given threat environment",
        processed_context=processed_context
    )
    
    print("🔧 Complete Prompt Structure:")
    print(f"  System prompt length: {len(system_prompt)} characters")
    print(f"  User prompt length: {len(user_prompt)} characters")
    print()
    
    print("📝 System Prompt Preview:")
    print(system_prompt[:400] + "..." if len(system_prompt) > 400 else system_prompt)
    print()
    
    print("📝 User Prompt Preview:")
    print(user_prompt[:400] + "..." if len(user_prompt) > 400 else user_prompt)
    print()
    
    # Check if LLM client can be initialized
    try:
        llm_client = LLMClient(primary_provider=LLMProvider.ANTHROPIC)
        
        print("🤖 LLM Client Status:")
        print(f"  Available providers: {list(llm_client.clients.keys())}")
        print(f"  Primary provider: {llm_client.primary_provider.value}")
        print()
        
        # Note: We won't actually call the LLM to avoid API costs
        print("📋 Simulated LLM Response Structure:")
        simulated_response = {
            "content": "Based on [DOC-PROC-001] and threat [THR-001], I recommend...",
            "model": "claude-sonnet-4-20250514",
            "provider": "anthropic",
            "tokens_used": 1250,
            "finish_reason": "end_turn",
            "citations": ["DOC-PROC-001", "THR-001", "AST-001"],
            "context_utilization": 0.75
        }
        
        print(json.dumps(simulated_response, indent=2))
        
    except Exception as e:
        print(f"⚠️  LLM Client initialization failed: {e}")
        print("   (This is expected if API keys are not configured)")


def analyze_log_files():
    """Analyze existing log files for LLM interactions."""
    print("=== LOG FILE ANALYSIS ===")
    print()
    
    log_files = [f for f in os.listdir('.') if f.endswith('.log')]
    
    if not log_files:
        print("📁 No log files found in current directory")
        return
    
    for log_file in log_files:
        print(f"📄 Analyzing: {log_file}")
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Look for LLM-related log entries
            llm_entries = []
            for line_num, line in enumerate(lines, 1):
                if any(keyword in line.lower() for keyword in [
                    'generated response', 'llm', 'prompt', 'tokens', 'anthropic', 'openai'
                ]):
                    llm_entries.append((line_num, line.strip()))
            
            if llm_entries:
                print(f"  Found {len(llm_entries)} LLM-related entries")
                print("  Recent entries:")
                for line_num, entry in llm_entries[-3:]:  # Show last 3
                    print(f"    Line {line_num}: {entry[:100]}...")
            else:
                print("  No LLM-related entries found")
            
        except Exception as e:
            print(f"  Error reading {log_file}: {e}")
        
        print()


def examine_response_structure():
    """Examine the structure of LLM responses."""
    print("=== LLM RESPONSE STRUCTURE ===")
    print()
    
    print("📊 LLMResponse Dataclass Fields:")
    print("  • content: str - The generated text response")
    print("  • model: str - Model used (e.g., 'claude-sonnet-4-20250514')")
    print("  • provider: LLMProvider - Provider enum (ANTHROPIC, OPENAI, GOOGLE)")
    print("  • tokens_used: int - Total tokens consumed")
    print("  • finish_reason: str - Why generation stopped")
    print("  • raw_response: Any - Full provider response object")
    print()
    
    print("🔄 Agent Response Dictionary:")
    print("  • success: bool - Whether generation succeeded")
    print("  • content: str - Generated content (parsed if structured)")
    print("  • citations: List[str] - Context element IDs referenced")
    print("  • context_utilization: float - Percentage of context used")
    print("  • tokens_used: int - Tokens consumed")
    print("  • model: str - Model used")
    print("  • provider: str - Provider used")
    print("  • processed_context_tokens: int - Context tokens provided")
    print("  • context_truncated: bool - Whether context was truncated")
    print()
    
    print("📈 Performance Metrics:")
    print("  • total_interactions: int - Total LLM calls")
    print("  • avg_tokens_per_interaction: float - Average token usage")
    print("  • avg_context_utilization: float - Average context usage")
    print("  • successful_interactions: int - Successful calls")
    print("  • failed_interactions: int - Failed calls")


def show_access_patterns():
    """Show common patterns for accessing prompts and responses."""
    print("=== ACCESS PATTERNS ===")
    print()
    
    print("🔍 Runtime Access During Agent Execution:")
    print("""
# Get agent response with full metadata
response = await agent.generate_with_context(
    task_description="Plan EW missions",
    max_tokens=4000,
    temperature=0.3
)

# Access response components
print(f"Success: {response['success']}")
print(f"Model: {response['model']}")
print(f"Provider: {response['provider']}")
print(f"Tokens used: {response['tokens_used']}")
print(f"Context utilization: {response['context_utilization']:.1%}")
print(f"Citations: {response['citations']}")
print(f"Content preview: {response['content'][:200]}...")
""")
    
    print("📊 Performance Analysis:")
    print("""
# Get agent performance statistics
if hasattr(agent, 'get_performance_stats'):
    stats = agent.get_performance_stats()
    print(f"Total interactions: {stats['total_interactions']}")
    print(f"Average tokens: {stats['avg_tokens_per_interaction']:.0f}")
    print(f"Success rate: {stats['success_rate']:.1%}")

# Semantic tracking analysis
if agent.semantic_tracker:
    semantic_stats = agent.get_semantic_stats()
    print(f"Context utilization: {semantic_stats['avg_utilization']:.1%}")
    
    underused = agent.get_underutilized_context()
    print(f"Underutilized elements: {len(underused)}")
""")
    
    print("📝 Log File Parsing:")
    print("""
import re
from datetime import datetime

def parse_llm_logs(log_file):
    llm_interactions = []
    
    with open(log_file, 'r') as f:
        for line in f:
            if 'Generated response' in line:
                # Extract timestamp, agent, tokens, etc.
                match = re.search(r'(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})', line)
                if match:
                    timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                    
                # Extract metrics
                tokens_match = re.search(r'(\\d+) tokens', line)
                tokens = int(tokens_match.group(1)) if tokens_match else 0
                
                llm_interactions.append({
                    'timestamp': timestamp,
                    'tokens': tokens,
                    'line': line.strip()
                })
    
    return llm_interactions

# Usage
interactions = parse_llm_logs('context_aware_demo.log')
print(f"Found {len(interactions)} LLM interactions")
""")


def main():
    """Main demonstration function."""
    print("=" * 80)
    print("LLM PROMPTS AND RESPONSES EXAMINATION")
    print("=" * 80)
    print()
    
    # 1. Examine prompt templates
    examine_prompt_templates()
    
    # 2. Build sample prompts
    build_sample_prompts()
    
    # 3. Examine context processing
    processed_context = examine_context_processing()
    
    # 4. Demonstrate LLM interaction
    demonstrate_llm_interaction(processed_context)
    
    # 5. Analyze log files
    analyze_log_files()
    
    # 6. Examine response structure
    examine_response_structure()
    
    # 7. Show access patterns
    show_access_patterns()
    
    print("=" * 80)
    print("SUMMARY: LLM PROMPTS AND RESPONSES LOCATIONS")
    print("=" * 80)
    print()
    
    print("📂 Source Code Locations:")
    print("  • Prompt templates: aether_os/prompt_builder.py")
    print("  • LLM client: aether_os/llm_client.py")
    print("  • Context processing: aether_os/context_processor.py")
    print("  • Agent interactions: aether_os/context_aware_agent.py")
    print()
    
    print("📊 Runtime Data Access:")
    print("  • Current context: agent.current_context")
    print("  • Response metadata: response['tokens_used'], response['citations']")
    print("  • Performance stats: agent.get_performance_stats()")
    print("  • Semantic tracking: agent.semantic_tracker")
    print()
    
    print("📋 Log Files:")
    log_files = [f for f in os.listdir('.') if f.endswith('.log')]
    for log_file in log_files:
        print(f"  • {log_file}")
    print()
    
    print("✅ All LLM interactions are fully transparent and accessible")
    print("✅ Prompts are constructed from configurable templates")
    print("✅ Responses include complete metadata and performance metrics")
    print("✅ Context processing is logged and trackable")
    print("✅ Citation tracking enables optimization")


if __name__ == "__main__":
    main()
