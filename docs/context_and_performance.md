# Context Management and Performance Evaluation

## Overview

Aether OS includes an advanced context management and performance evaluation system that ensures agents have appropriate situational awareness while optimizing their effectiveness.

## Architecture

### Components

1. **AgentContextManager** - Builds and manages dynamic context windows
2. **AgentPerformanceEvaluator** - Evaluates agent performance across multiple dimensions
3. **ContextPerformanceFeedback** - Feedback loop that optimizes context based on performance

### Context Management

#### Dynamic Context Windows

Agents receive role-appropriate context tailored to their current phase and task:

- **Doctrinal Context**: Relevant procedures, policies, and best practices
- **Situational Context**: Current threats, assets, missions, spectrum status
- **Historical Context**: Lessons learned, past performance, recurring issues
- **Collaborative Context**: Peer agent states, shared artifacts, pending requests

#### Phase-Based Templates

Context provisioning adapts to ATO cycle phases:

```python
PHASE_CONTEXT_TEMPLATES = {
    "PHASE3_WEAPONEERING": {
        "ew_planner_agent": {
            "doctrine_priority": ["mission_planning", "asset_assignment"],
            "threat_detail_level": "tactical",
            "asset_visibility": "detailed",
            "historical_depth": 1,
        }
    }
}
```

#### Token Budget Management

- Default max context: 32,000 tokens
- Automatic pruning by relevance if exceeded
- Priority: Doctrine > Situational > Collaborative > Historical

## Performance Evaluation

### Six Evaluation Dimensions

1. **Mission Effectiveness** (30% weight)
   - Mission success rate
   - Output quality score
   - Doctrinal compliance rate

2. **Efficiency** (20% weight)
   - Average task completion time
   - Timeline adherence rate
   - Resource utilization

3. **Collaboration** (15% weight)
   - Inter-agent response time
   - Coordination effectiveness
   - Information sharing quality

4. **Process Improvement** (15% weight)
   - Inefficiencies identified
   - Improvement suggestions
   - Suggestion adoption rate

5. **Learning & Adaptation** (10% weight)
   - Lesson learned application
   - Performance trend
   - Context utilization

6. **Robustness** (10% weight)
   - Error rate
   - Recovery success rate
   - Escalation appropriateness

### Metrics Calculated

For each ATO cycle, 18 metrics are calculated per agent:

```python
@dataclass
class AgentPerformanceMetrics:
    # Mission Effectiveness
    mission_success_rate: float
    output_quality_score: float
    doctrinal_compliance_rate: float

    # Efficiency
    avg_task_completion_time: float
    timeline_adherence_rate: float
    resource_utilization: float

    # ... (12 more metrics)

    overall_score: float  # Weighted average
```

## Context-Performance Feedback Loop

### Optimization Strategy

The system analyzes performance and automatically adjusts context provisioning:

| Performance Pattern | Context Adjustment |
|---------------------|-------------------|
| Low context utilization (<50%) | Reduce context size by 30% |
| High utilization + low quality | Improve context quality |
| High error rate (>10%) | Expand doctrinal context by 30% |
| Poor coordination (<70%) | Expand collaborative context by 20% |
| Low success rate (<80%) | Expand situational context by 30% |
| Slow response time (>10 min) | Enable priority caching |

### Pattern Analysis

The system identifies:
- High-performing context strategies
- Low-performing context configurations
- Correlation between context utilization and output quality
- Optimization opportunities

## Usage

### For Agents

Agents automatically receive context through the base class:

```python
class MyAgent(BaseAetherAgent):
    def my_procedure(self, cycle_id: str):
        # Request context
        context = self.request_context(
            task_description="Planning EW missions",
            max_context_size=32000
        )

        # Use context
        threats = context.situational_context.current_threats
        doctrine = context.doctrinal_context.relevant_procedures

        # Track usage
        self.reference_context_item("situational:threats")
        self.reference_context_item("doctrine:AFI-10-703")

        # ... perform task ...

        # Finalize tracking
        self.finalize_context_usage(result={"missions_planned": 5})
```

### For AetherOS

The core system provides high-level interfaces:

```python
# Build context for an agent
context = aether_os.build_agent_context(
    agent_id="ew_planner_agent",
    current_task="Plan EW missions",
    max_context_size=32000
)

# Evaluate performance
metrics = aether_os.evaluate_agent_performance(
    agent_id="ew_planner_agent",
    cycle_id="ATO-001"
)

# Get reports
performance_report = aether_os.get_performance_report(
    agent_id="ew_planner_agent",
    cycles=5
)

optimization_report = aether_os.get_context_optimization_report()

analysis = aether_os.get_context_performance_analysis()
```

## Running Evaluation

Use the performance evaluation script:

```bash
cd aether-project
./venv/bin/python scripts/evaluate_performance.py
```

This will:
1. Execute a complete ATO cycle
2. Evaluate all agent performance
3. Generate optimization recommendations
4. Analyze context-performance correlations
5. Produce comprehensive reports

## Context Refresh Triggers

Context is automatically refreshed when:

- **Phase Transition**: New phase begins
- **New Intelligence**: Significant threat data update
- **Task Change**: Agent assigned new task
- **Periodic**: Every N hours (configurable)
- **Manual**: Explicit refresh request

## Best Practices

### For Agent Development

1. **Always request context** at the start of major procedures
2. **Track context usage** by referencing items you actually use
3. **Finalize tracking** after task completion
4. **Use context efficiently** - don't request more than needed

### For System Operators

1. **Monitor context utilization** - low utilization indicates over-provisioning
2. **Review performance trends** - identify degrading agents early
3. **Apply optimization recommendations** - let the system guide improvements
4. **Analyze patterns** - learn which context strategies work best

## Performance Report Example

```
================================================================
AGENT PERFORMANCE REPORT: ew_planner_agent
Period: Last 1 cycle(s)
================================================================

MISSION EFFECTIVENESS
---------------------
Success Rate: 100.0%
Output Quality: 0.50/1.0
Doctrinal Compliance: 95.0%

EFFICIENCY
----------
Avg Completion Time: 1.00x expected
Timeline Adherence: 100.0%
Resource Utilization: 0.80/1.0

COLLABORATION
-------------
Response Time: 5.0 minutes
Coordination Score: 0.85/1.0
Information Sharing: 0.80/1.0

PROCESS IMPROVEMENT (Option C)
-------------------------------
Inefficiencies Flagged: 0
Improvement Suggestions: 0
Adoption Rate: 50.0%

LEARNING & ADAPTATION
---------------------
Lesson Application: 70.0%
Performance Trend: stable
Context Utilization: 50.0%

ROBUSTNESS
----------
Error Rate: 0.0%
Recovery Success: 90.0%
Escalation Quality: 0.85/1.0

OVERALL SCORE: 0.74/1.0
================================================================
```

## Future Enhancements

Planned improvements:

1. **Adaptive context templates** based on historical performance
2. **Multi-cycle learning** to predict optimal context configurations
3. **Cross-agent context sharing** for better collaboration
4. **Real-time context adjustment** during task execution
5. **LLM-based context quality assessment**
