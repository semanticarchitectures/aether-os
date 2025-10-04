# Agent Testing Framework

## Overview

The Agent Testing Framework provides a controlled environment for evaluating individual agent performance with custom contexts, messages, and automated evaluation.

## Architecture

### Components

1. **AgentTestScenario** - Defines test configuration
   - Custom context (threats, assets, doctrine)
   - Test messages to send
   - Evaluation criteria

2. **AgentTestRunner** - Executes test scenarios
   - Builds custom context
   - Sends messages to agent
   - Records responses
   - Tracks context utilization

3. **EvaluatorAgent** - Evaluates responses
   - LLM-based or rule-based evaluation
   - Criterion-specific scoring
   - Pass/fail determination
   - Detailed feedback

## Usage

### Running Tests

```bash
python scripts/test_agent.py
```

This will:
1. Load example test scenarios
2. Execute tests on configured agents
3. Evaluate responses using EvaluatorAgent
4. Generate comprehensive test report

### Creating Custom Scenarios

```python
from aether_os.agent_testing import AgentTestScenario, TestContext, TestMessage
from aether_os.orchestrator import ATOPhase

scenario = AgentTestScenario(
    scenario_id="custom_test_001",
    name="My Custom Test",
    description="Test agent behavior in specific scenario",
    agent_id="ew_planner_agent",

    # Configure context
    context=TestContext(
        phase=ATOPhase.PHASE3_WEAPONEERING,
        task_description="Plan EW missions",
        threats=[
            {
                "threat_id": "SAM-001",
                "threat_type": "SA-6",
                "location": {"lat": 35.0, "lon": 45.0},
            }
        ],
        assets=[
            {
                "asset_id": "EA-001",
                "platform": "EA-18G",
                "capability": "Stand-in jamming",
            }
        ],
        doctrinal_procedures=[
            "Assign assets to missions",
            "Check for fratricide",
        ],
    ),

    # Define test messages
    messages=[
        TestMessage(
            message_type="plan_missions",
            payload={
                "targets": ["SAM-001"],
                "timeframe": "H-hour to H+2",
            },
            description="Request mission planning",
        ),
    ],

    # Evaluation criteria
    evaluation_criteria={
        "mission_completion": {
            "type": "completion",
            "weight": 0.5,
            "target": 1.0,
        },
        "asset_utilization": {
            "type": "quality",
            "weight": 0.3,
            "target": 0.8,
        },
        "doctrinal_compliance": {
            "type": "compliance",
            "weight": 0.2,
            "target": 0.9,
        },
    },

    tags=["custom", "ew_planning"],
    difficulty="medium",
)
```

### Programmatic Testing

```python
import asyncio
from aether_os.core import AetherOS
from aether_os.agent_testing import AgentTestRunner
from agents.ew_planner_agent import EWPlannerAgent
from agents.evaluator_agent import EvaluatorAgent

async def run_test():
    # Initialize
    aether_os = AetherOS()
    agent = EWPlannerAgent(aether_os)
    evaluator = EvaluatorAgent(aether_os)

    # Create test runner
    runner = AgentTestRunner(
        aether_os=aether_os,
        evaluator_agent=evaluator,
    )

    # Run scenario
    result = await runner.run_scenario(scenario, agent)

    # Check results
    print(f"Passed: {result.passed}")
    print(f"Score: {result.evaluation_score:.2f}")
    print(f"Feedback: {result.evaluation_feedback}")

asyncio.run(run_test())
```

## Test Context Configuration

### Available Context Components

**Doctrinal Context**:
```python
context = TestContext(
    doctrinal_procedures=[
        "Follow JCEOI process",
        "Coordinate with all spectrum users",
    ],
)
```

**Situational Context**:
```python
context = TestContext(
    threats=[
        {"threat_id": "T-001", "type": "SAM", "location": {...}},
    ],
    assets=[
        {"asset_id": "A-001", "platform": "EA-18G", ...},
    ],
    missions=[
        {"mission_id": "M-001", "type": "SEAD", ...},
    ],
)
```

**Historical Context**:
```python
context = TestContext(
    historical_lessons=[
        "Coordinate spectrum early to avoid conflicts",
        "Validate mission approvals before publication",
    ],
)
```

**Phase Context**:
```python
context = TestContext(
    phase=ATOPhase.PHASE3_WEAPONEERING,
    task_description="Plan EW missions for SEAD",
)
```

## Evaluation Criteria

### Criterion Types

**completion** - Task completion rate
- Measures if all requested tasks were completed
- Score: 0.0-1.0

**quality** - Response quality
- Evaluates completeness and appropriateness
- Score: 0.0-1.0

**compliance** - Doctrinal compliance
- Checks adherence to procedures
- Score: 0.0-1.0

**utilization** - Context utilization
- Measures effective use of provided context
- Score: 0.0-1.0 (actual utilization rate)

**speed** - Response time
- Evaluates execution speed
- Score: 0.0-1.0

### Criterion Configuration

```python
evaluation_criteria={
    "criterion_name": {
        "type": "quality",           # Criterion type
        "weight": 0.4,               # Weight in overall score
        "target": 0.8,               # Target/threshold
        "description": "...",        # Description
    },
}
```

### Overall Scoring

Overall score = Weighted average of all criterion scores

```
overall_score = Σ(criterion_score × weight) / Σ(weights)
```

**Pass threshold**: 0.7 (default)

## EvaluatorAgent

### Evaluation Modes

**LLM-based** (when Anthropic API available):
- Uses Claude to evaluate responses
- Provides detailed, nuanced feedback
- Understands context and intent
- Generates criterion-specific scores

**Rule-based** (fallback):
- Uses heuristics to score responses
- Success rate, completeness checks
- Keyword matching for compliance
- Faster but less nuanced

### Evaluation Process

1. **Receive evaluation request** with:
   - Scenario details
   - Agent responses
   - Evaluation criteria
   - Context utilization

2. **Analyze responses** against each criterion

3. **Generate scores**:
   - Individual criterion scores
   - Weighted overall score
   - Pass/fail determination

4. **Provide feedback**:
   - Strengths identified
   - Weaknesses noted
   - Recommendations for improvement

## Test Results

### AgentTestResult Fields

```python
result = AgentTestResult(
    scenario_id="test_001",
    agent_id="ew_planner_agent",

    # Execution metrics
    messages_sent=3,
    responses_received=3,
    execution_time_seconds=1.2,

    # Evaluation results
    evaluation_score=0.85,
    passed=True,
    criteria_scores={
        "completion": 1.0,
        "quality": 0.8,
        "compliance": 0.75,
    },
    evaluation_feedback="Agent performed well...",

    # Context usage
    context_utilization=0.72,

    # Response log
    response_log=[...],

    # Errors
    errors=[],
)
```

### Report Generation

```python
# Generate report for all tests
report = test_runner.generate_test_report()

# Generate report for specific scenario
report = test_runner.generate_test_report(scenario_id="test_001")
```

Report includes:
- Individual test results
- Criterion scores
- Evaluation feedback
- Summary statistics (if multiple tests)
  - Average score
  - Pass rate
  - Total tests run

## Best Practices

### Scenario Design

1. **Start simple** - Begin with straightforward scenarios
2. **Isolate behavior** - Test one capability at a time
3. **Vary difficulty** - Create easy, medium, and hard scenarios
4. **Use realistic data** - Provide context similar to production

### Context Configuration

1. **Be specific** - Provide relevant, targeted context
2. **Match phase** - Align context with agent's expected phase
3. **Size appropriately** - Don't overload with unnecessary data
4. **Include doctrine** - Always provide relevant procedures

### Evaluation Criteria

1. **Measure what matters** - Focus on key capabilities
2. **Weight appropriately** - More important criteria get higher weights
3. **Set realistic targets** - Based on expected performance
4. **Include compliance** - Always check doctrinal adherence

### Interpreting Results

1. **Context utilization** - Low (<50%) may indicate:
   - Over-provisioned context
   - Agent not referencing relevant info
   - Missing tracking calls

2. **Low scores** - Investigate:
   - Criterion-specific scores to identify weaknesses
   - Evaluation feedback for specific issues
   - Response log for actual agent behavior

3. **Errors** - Check:
   - Agent error handling
   - Message format compatibility
   - Context validity

## Example Scenarios

See `scripts/test_agent.py` for complete examples:

1. **EMS Strategy Development** - High threat environment
2. **EW Mission Planning** - Multi-target assignment
3. **Spectrum Management** - Conflict resolution

## Integration with Performance Evaluation

Test results can inform the broader performance evaluation system:

```python
# Run test
result = await test_runner.run_scenario(scenario, agent)

# Feed into performance metrics
if result.passed:
    # Update agent's success rate
    # Track quality scores
    # Record context utilization
```

## Future Enhancements

Planned improvements:
- YAML-based scenario definitions
- Scenario libraries by agent role
- Automated regression testing
- Performance benchmarking
- Comparative agent evaluation
