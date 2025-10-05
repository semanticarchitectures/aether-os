# LLM Prompts and Responses Storage Guide

## Overview

This guide explains where LLM prompts and responses are stored, how to access them, and how to analyze LLM interactions in the Aether OS system.

## 🏗️ Architecture Overview

The LLM interaction system consists of four main components:

1. **Prompt Construction** (`aether_os/prompt_builder.py`)
2. **LLM Client** (`aether_os/llm_client.py`) 
3. **Context Processing** (`aether_os/context_processor.py`)
4. **Agent Interaction** (`aether_os/context_aware_agent.py`)

## 📝 1. Prompt Construction

### Location: `aether_os/prompt_builder.py`

**Key Components:**
- `BASE_SYSTEM_PROMPT` - Core instructions for all agents
- `ROLE_PROMPTS` - Role-specific instructions (ems_strategy, ew_planner, etc.)
- `TASK_TEMPLATES` - Reusable task templates

**Available Task Templates:**
- `develop_strategy` - EMS strategy development (329 chars)
- `plan_missions` - EW mission planning (332 chars)
- `allocate_frequencies` - Frequency allocation (278 chars)
- `produce_ato` - ATO production (273 chars)
- `assess_cycle` - Performance assessment (309 chars)

**Key Methods:**
- `build_prompt()` - Constructs complete prompt with context
- `build_simple_prompt()` - Quick prompt without full context
- `_build_system_prompt()` - Role-specific system prompt
- `_build_user_prompt()` - Task + context user prompt

**Example System Prompt Structure:**
```
You are an AI agent in the USAF Air Operations Center (AOC) supporting 
Electromagnetic Spectrum (EMS) Operations.

Your role is to assist with ATO (Air Tasking Order) cycle operations while 
strictly adhering to USAF doctrine and procedures.

CRITICAL REQUIREMENTS:
1. Ground ALL decisions in provided doctrinal context
2. Cite specific context elements using their IDs (e.g., [DOC-001], [THR-001])
3. Flag information gaps - if you need info not provided, explicitly state it
4. Follow procedures exactly as documented
...
```

## 🤖 2. LLM Client & Response Structure

### Location: `aether_os/llm_client.py`

**LLMResponse Dataclass Fields:**
- `content: str` - Generated text response
- `model: str` - Model used (claude-sonnet-4, gpt-4o, etc.)
- `provider: LLMProvider` - Provider enum (ANTHROPIC, OPENAI, GOOGLE)
- `tokens_used: int` - Total tokens consumed
- `finish_reason: str` - Why generation stopped
- `raw_response: Any` - Full provider response object

**Supported Providers:**
- `anthropic` - Claude Sonnet 4.5 (primary)
- `openai` - GPT-4o (alternative)
- `google` - Gemini Pro (alternative)

**Key Methods:**
- `generate()` - Main generation method with retry logic
- `_generate_anthropic()` - Anthropic-specific generation
- `_generate_openai()` - OpenAI-specific generation
- `_generate_google()` - Google-specific generation

## 📊 3. Context Processing

### Location: `aether_os/context_processor.py`

**ProcessedContext Dataclass Fields:**
- `doctrinal_context: str` - Formatted doctrine text
- `situational_context: str` - Current threats/assets
- `historical_context: str` - Past performance data
- `collaborative_context: str` - Other agents' outputs
- `total_tokens: int` - Token count
- `element_ids: List[str]` - Referenced context element IDs
- `truncated: bool` - Whether context was truncated

**Token Budget Allocation:**
- 40% - Doctrinal context
- 30% - Situational context
- 20% - Historical context
- 10% - Collaborative context

## 🔄 4. Agent Interaction Flow

### Location: `aether_os/context_aware_agent.py`

**LLM Interaction Process:**
1. `agent.generate_with_context(task_description)` - Agent called
2. `ContextProcessor.process()` - Context processed and formatted
3. `PromptBuilder.build_prompt()` - Prompt built with role + task + context
4. `LLMClient.generate()` - LLM called with prompt
5. Response processed - Citations extracted, usage tracked
6. Result returned - Success, content, citations, utilization

**Agent Response Dictionary:**
- `success: bool` - Whether generation succeeded
- `content: str` - Generated content (parsed if structured)
- `citations: List[str]` - Context element IDs referenced
- `context_utilization: float` - Percentage of context used
- `tokens_used: int` - Tokens consumed
- `model: str` - Model used
- `provider: str` - Provider used
- `processed_context_tokens: int` - Context tokens provided
- `context_truncated: bool` - Whether context was truncated

## 📋 5. Logging and Storage

### Log Files

**Available Log Files:**
- `agent_testing.log` - Agent testing and evaluation
- `performance_evaluation.log` - Performance metrics
- `full_ato_cycle_demo.log` - Full ATO cycle demonstrations
- `ato_cycle_run.log` - ATO cycle execution logs
- `yaml_scenario_test.log` - YAML scenario testing
- `context_aware_demo.log` - Context-aware agent demonstrations

### What Gets Logged

**Prompt Construction:**
```
Built prompt for role=ew_planner, task=Plan EW missions
```

**Context Processing:**
```
Processing context (max tokens: 4000)
Built test context: 138 tokens (max: 20000)
```

**LLM Generation:**
```
Successfully generated response with anthropic
```

**Response Analysis:**
```
Generated response: 1250 tokens, 3 citations, 75.0% utilization
```

**Performance Metrics:**
```
Context utilization: 75.0%
Total interactions: 15
Average tokens per interaction: 1150
```

## 🔍 6. Accessing Prompts & Responses

### Runtime Access During Agent Execution

```python
# Execute agent task
response = await agent.generate_with_context("Plan EW missions")

# Access response metadata
print(f"Model: {response['model']}")
print(f"Tokens: {response['tokens_used']}")
print(f"Citations: {response['citations']}")
print(f"Utilization: {response['context_utilization']:.1%}")
print(f"Content: {response['content'][:200]}...")
```

### Performance Analysis

```python
# Get agent performance statistics
if hasattr(agent, 'get_performance_stats'):
    stats = agent.get_performance_stats()
    print(f"Total interactions: {stats['total_interactions']}")
    print(f"Average tokens: {stats['avg_tokens_per_interaction']:.0f}")
    print(f"Success rate: {stats['success_rate']:.1%}")
```

### Context Inspection

```python
# Inspect current agent context
context = agent.current_context
if context:
    print(f"Phase: {context.current_phase}")
    print(f"Task: {context.current_task}")
    print(f"Elements: {len(context.referenced_items)}")
```

### Semantic Tracking Analysis

```python
# Analyze context usage patterns
if agent.semantic_tracker:
    semantic_stats = agent.get_semantic_stats()
    print(f"Context utilization: {semantic_stats['avg_utilization']:.1%}")
    
    underused = agent.get_underutilized_context()
    print(f"Underutilized elements: {len(underused)}")
    for elem in underused[:3]:
        print(f"  - {elem.element_id}: {elem.content[:50]}...")
```

## 📄 7. Log File Analysis

### Parsing LLM Interactions

```python
import re
from datetime import datetime

def parse_llm_logs(log_file):
    llm_interactions = []
    
    with open(log_file, 'r') as f:
        for line in f:
            if 'Generated response' in line:
                # Extract timestamp
                match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if match:
                    timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                
                # Extract metrics
                tokens_match = re.search(r'(\d+) tokens', line)
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
```

### Analyzing Context Usage

```python
def analyze_context_usage(log_file):
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    context_lines = [line for line in lines if 'Built test context' in line]
    
    for line in context_lines:
        tokens_match = re.search(r'(\d+) tokens', line)
        if tokens_match:
            tokens = int(tokens_match.group(1))
            print(f"Context size: {tokens} tokens")
```

## 🔧 8. Direct Prompt Building Example

```python
from aether_os.prompt_builder import PromptBuilder
from aether_os.context_processor import ContextProcessor

# Initialize components
builder = PromptBuilder()
processor = ContextProcessor()

# Build prompt directly
system_prompt, user_prompt = builder.build_prompt(
    role="ew_planner",
    task_description="Plan EW missions for high-threat environment",
    processed_context=processed_context
)

print("SYSTEM PROMPT:")
print(system_prompt)
print("\nUSER PROMPT:")
print(user_prompt)
```

## 📈 9. Performance Metrics

### Agent Performance Tracking

**Metrics Collected:**
- Total LLM interactions
- Average tokens per interaction
- Context utilization rates
- Success/failure rates
- Response times
- Citation accuracy

**Access Methods:**
```python
# Get comprehensive performance stats
stats = agent.get_performance_stats()

# Get semantic tracking metrics
semantic_stats = agent.get_semantic_stats()

# Get underutilized context elements
underused = agent.get_underutilized_context()
```

## 📂 10. Storage Locations Summary

### Code Locations
- **Prompt templates:** `aether_os/prompt_builder.py`
- **LLM responses:** `aether_os/llm_client.py`
- **Context processing:** `aether_os/context_processor.py`
- **Agent interactions:** `aether_os/context_aware_agent.py`

### Runtime Data
- **Current context:** `agent.current_context`
- **Response metadata:** `response['tokens_used']`, `response['citations']`
- **Performance stats:** `agent.get_performance_stats()`
- **Semantic tracking:** `agent.semantic_tracker`

### Log Files
- All `.log` files in project root contain LLM interaction logs
- Searchable by keywords: "Generated response", "tokens", "citations", "utilization"

## ✅ Summary

**LLM prompts and responses in Aether OS are:**
- ✅ **Fully transparent** - All prompt construction is visible and configurable
- ✅ **Completely captured** - All responses include metadata and performance metrics
- ✅ **Thoroughly logged** - All interactions are logged with context and timing
- ✅ **Easily accessible** - Runtime access to all prompts, responses, and metrics
- ✅ **Continuously tracked** - Performance and usage patterns are monitored
- ✅ **Citation-enabled** - Context usage is tracked and optimizable

The system provides complete visibility into LLM interactions while maintaining the flexibility to analyze, optimize, and debug agent performance.
