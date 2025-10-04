# Aether OS - AI-Mediated Operating System for USAF EMS Operations

**Aether OS** is an AI-mediated operating system layer between USAF Air Operations Center (AOC) personnel and organizational assets for Electromagnetic Spectrum (EMS) Operations.

## Overview

Aether OS provides intelligent agent orchestration based on the 72-hour Air Tasking Order (ATO) cycle, with:

- **5 Specialized AOC Agents** for different ATO phases
- **Context-Aware Authorization** with role-based and phase-based access control
- **Process Improvement Tracking** - agents follow doctrine but flag inefficiencies
- **Information Access Brokering** with privacy controls and sanitization
- **Hub-and-Spoke Architecture** with central Context Knowledge Base (CKB)

## Key Innovation: Option C - Doctrine Compliance with Process Improvement

Agents **strictly follow USAF doctrine** BUT systematically identify:
- ✅ Redundant coordination steps
- ✅ Information gaps
- ✅ Timing constraints
- ✅ Doctrine contradictions
- ✅ Automation opportunities
- ✅ Deconfliction issues
- ✅ Resource bottlenecks

This enables continuous process improvement while maintaining doctrinal compliance.

## Architecture

### 5 AOC Agents

1. **EMS Strategy Agent** (Phase 1-2)
   - Develops EMS strategy from JFACC guidance
   - Access Level: SENSITIVE

2. **Spectrum Manager Agent** (Phase 3, 5)
   - Manages frequency allocation and deconfliction
   - Access Level: OPERATIONAL

3. **EW Planner Agent** (Phase 3)
   - Plans Electronic Warfare missions
   - Access Level: SENSITIVE

4. **ATO Producer Agent** (Phase 4)
   - Integrates EMS into Air Tasking Order
   - Access Level: SENSITIVE

5. **Assessment Agent** (Phase 6)
   - Assesses effectiveness and generates lessons learned
   - Access Level: OPERATIONAL

### ATO Cycle Phases (72 hours)

| Phase | Duration | Offset | Active Agents |
|-------|----------|--------|---------------|
| Phase 1: OEG | 6h | 0h | EMS Strategy |
| Phase 2: Target Development | 8h | 6h | EMS Strategy |
| Phase 3: Weaponeering | 10h | 14h | EW Planner, Spectrum Manager |
| Phase 4: ATO Production | 6h | 24h | ATO Producer, Spectrum Manager |
| Phase 5: Execution | 24h | 30h | Spectrum Manager |
| Phase 6: Assessment | 18h | 54h | Assessment |

## Installation

### Prerequisites

- Python 3.11+
- MongoDB (optional for full functionality)
- Open Policy Agent (OPA)

### Setup

```bash
# Clone repository
cd aether-project

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Seed test data
python scripts/seed_test_data.py

# Run ATO cycle simulation
python scripts/run_ato_cycle.py
```

### Install OPA

```bash
# macOS
brew install opa

# Linux
wget https://openpolicyagent.org/downloads/latest/opa_linux_amd64 -O opa
chmod +x opa

# Run OPA server
opa run --server --addr localhost:8181 policies/
```

## Quick Start

### Run ATO Cycle Simulation

```bash
python scripts/run_ato_cycle.py
```

This will:
1. Initialize Aether OS
2. Register all 5 agents
3. Execute all 6 ATO phases
4. Generate process improvement report
5. Output lessons learned

### Run Performance Evaluation

```bash
python scripts/evaluate_performance.py
```

This will:
1. Execute complete ATO cycle
2. Evaluate all agent performance (18 metrics per agent)
3. Generate context optimization recommendations
4. Analyze context-performance correlations
5. Produce comprehensive reports

### Run Agent Testing

```bash
python scripts/test_agent.py
```

This will:
1. Load test scenarios with custom contexts
2. Execute controlled tests on individual agents
3. Use EvaluatorAgent to score responses
4. Generate detailed test reports with feedback

Test individual agents in controlled scenarios with custom threats, assets, and evaluation criteria.

## Configuration

### Agent Profiles

Agent access profiles are configured in `config/agent_profiles.yaml`

### Access Policies

Information access policies are in `config/access_policies.yaml`

### ATO Schedule

Phase timing and agent activation in `config/ato_schedule.yaml`

## Project Structure

```
aether-project/
├── aether_os/              # Core framework
│   ├── core.py             # Main AetherOS class
│   ├── access_control.py   # Access control system
│   ├── authorization.py    # Multi-factor authorization
│   ├── information_broker.py
│   ├── process_improvement.py
│   ├── orchestrator.py     # ATO cycle orchestration
│   ├── doctrine_kb.py      # Doctrine knowledge base
│   ├── agent_context.py    # Context data structures
│   ├── context_manager.py  # Context provisioning
│   ├── performance_metrics.py
│   ├── performance_evaluator.py
│   └── context_feedback.py # Performance feedback loop
│
├── agents/                 # AOC agents
│   ├── base_agent.py       # Base with context support
│   ├── ems_strategy_agent.py
│   ├── spectrum_manager_agent.py
│   ├── ew_planner_agent.py
│   ├── ato_producer_agent.py
│   └── assessment_agent.py
│
├── mcp_servers/            # MCP tool servers
│   ├── doctrine_server.py
│   ├── spectrum_server.py
│   ├── threat_intel_server.py
│   └── asset_tracking_server.py
│
├── policies/               # OPA policies
│   ├── agent_authorization.rego
│   └── phase_constraints.rego
│
├── config/                 # Configuration
│   ├── agent_profiles.yaml
│   ├── access_policies.yaml
│   └── ato_schedule.yaml
│
├── scripts/                # Utility scripts
│   ├── run_ato_cycle.py
│   ├── evaluate_performance.py
│   └── seed_test_data.py
│
└── docs/                   # Documentation
    ├── architecture.md
    ├── agent_guide.md
    └── context_and_performance.md
```

## Features

### Access Control

**NOT DoD Classification** - Custom organizational tiers:
- PUBLIC (1)
- INTERNAL (2)
- OPERATIONAL (3)
- SENSITIVE (4)
- CRITICAL (5)

### Authorization

6-Factor Authorization:
1. Role authority
2. Phase appropriateness
3. Information access
4. Delegation chain
5. Doctrinal compliance
6. OPA policy evaluation

### Context Management

**Dynamic Context Windows** - Agents receive role-appropriate context tailored to phase and task:
- **Doctrinal Context**: Relevant procedures, policies, best practices
- **Situational Context**: Current threats, assets, missions, spectrum
- **Historical Context**: Lessons learned, performance patterns
- **Collaborative Context**: Peer states, shared artifacts

**Phase-Based Templates** optimize context for each ATO phase with automatic token budget management (max 32K tokens).

### Performance Evaluation

**Multi-Dimensional Assessment** across 6 categories:
1. **Mission Effectiveness** (30%) - Success rate, quality, compliance
2. **Efficiency** (20%) - Task time, resource utilization
3. **Collaboration** (15%) - Response time, coordination
4. **Process Improvement** (15%) - Inefficiencies flagged, suggestions
5. **Learning & Adaptation** (10%) - Trend, context utilization
6. **Robustness** (10%) - Error rate, recovery

**Context-Performance Feedback Loop** automatically optimizes context provisioning based on performance metrics.

### Process Improvement

Tracks 7 types of inefficiencies:
- Redundant coordination
- Information gaps
- Timing constraints
- Doctrine contradictions
- Automation opportunities
- Deconfliction issues
- Resource bottlenecks

### Information Broker

Centralized information access with:
- Access control enforcement
- Data sanitization based on access level
- Audit logging
- MCP server routing

## API Examples

### Query Doctrine

```python
from aether_os.core import AetherOS
from aether_os.access_control import InformationCategory

aether = AetherOS()

result = aether.query_information(
    agent_id="ems_strategy_agent",
    category=InformationCategory.DOCTRINE,
    query_params={"query": "EMS strategy development"},
)
```

### Authorize Action

```python
authorized = aether.authorize_action(
    agent_id="spectrum_manager_agent",
    action="allocate_frequency",
    context={
        "frequency_range": (2400.0, 2500.0),
        "time_window": ("2025-10-04T10:00:00Z", "2025-10-04T14:00:00Z"),
    },
)
```

### Get Process Improvement Report

```python
report = aether.get_process_improvement_report()
print(report)
```

## Technology Stack

- **Python 3.11+** - Core framework
- **Anthropic Claude Sonnet 4.5** - Primary LLM
- **ChromaDB** - Vector database for doctrine
- **MongoDB** - Operational data storage (optional)
- **Open Policy Agent** - Authorization policies
- **FastAPI** - API framework
- **MCP (Model Context Protocol)** - Tool integration

## Development

### Running Tests

```bash
# OPA policy tests
opa test policies/

# Python tests (TODO: implement)
pytest tests/
```

### Logging

Logs are written to both console and `ato_cycle_run.log`

## Limitations (Prototype)

This is a **prototype** implementation:
- ✅ Full agent orchestration
- ✅ Process improvement tracking
- ✅ Access control and authorization
- ✅ Doctrine knowledge base
- ⚠️  Simplified MCP server implementations
- ⚠️  Mock threat/asset data
- ⚠️  No MongoDB integration (in-memory fallback)
- ⚠️  Simplified geospatial operations

## Future Enhancements

- Full MCP server implementations
- MongoDB integration
- Real-time ATO cycle execution
- Web-based dashboard
- Integration with actual USAF systems
- Advanced geospatial analysis
- Multi-agent negotiation protocols

## License

This is a prototype for research and demonstration purposes.

## Contributing

This is a demonstration project. For production use, contact the development team.

## References

- AFI 10-703: Electronic Warfare Integrated Reprogramming
- JP 3-13.1: Electronic Warfare
- USAF AOC processes and procedures

---

**🤖 Generated with Claude Code** - An AI-mediated operating system for USAF EMS Operations
