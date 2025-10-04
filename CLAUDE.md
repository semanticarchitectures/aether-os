# Aether OS for USAF EMS Operations - Claude Code Directive

## Project Overview

Generate a complete, production-ready prototype of **Aether OS**: an AI-mediated operating system layer between USAF Air Operations Center (AOC) personnel and organizational assets for Electromagnetic Spectrum (EMS) Operations.

## Core Concept

Aether OS sits between humans and organizational assets (databases, systems, physical infrastructure), providing:
- **Intelligent agent orchestration** based on ATO (Air Tasking Order) cycle phases
- **Context-aware authorization** with role-based and phase-based access control
- **Process improvement tracking** - agents follow doctrine but flag inefficiencies (Option C)
- **Information access brokering** with privacy controls and sanitization

## Key Requirements

### 1. Architecture
- **Hub-and-spoke model**: Central Context Knowledge Base (CKB) with agents as spokes
- **ATO Cycle Orchestrator**: Acts as "process scheduler" - activates agents based on 72-hour ATO cycle phases
- **Hybrid doctrine compliance**: Agents strictly follow USAF doctrine BUT flag inefficiencies, contradictions, and automation opportunities
- **Flexible access control**: NOT DoD classification - custom organizational tiers (PUBLIC, INTERNAL, OPERATIONAL, SENSITIVE, CRITICAL)

### 2. Five AOC Agents

#### Agent 1: EMS Strategy Agent
- **Active Phases**: Phase 1 (OEG), Phase 2 (Target Development)
- **Role**: Develops EMS strategy from JFACC guidance
- **Responsibilities**:
  - Interpret commander's intent
  - Develop EMS concept of operations
  - Identify EMS objectives and effects
- **Access Level**: SENSITIVE
- **Information Needs**: Doctrine, threat data, organizational data, process metrics

#### Agent 2: Spectrum Manager Agent
- **Active Phases**: Phase 3 (Weaponeering), Phase 5 (Execution)
- **Role**: Manages frequency allocation and deconfliction
- **Responsibilities**:
  - Allocate frequencies to missions (following JCEOI process)
  - Deconflict spectrum usage
  - Coordinate with other spectrum users
  - Emergency reallocation during execution
- **Access Level**: OPERATIONAL
- **Information Needs**: Doctrine, spectrum allocations, asset status, threat frequencies

#### Agent 3: EW Planner Agent
- **Active Phases**: Phase 3 (Weaponeering)
- **Role**: Plans Electronic Warfare missions
- **Responsibilities**:
  - Translate EMS strategy into specific missions
  - Assign EMS assets to missions
  - Request frequency allocations
  - Ensure EA/EP/ES integration
  - Check for EA/SIGINT fratricide
- **Access Level**: SENSITIVE
- **Information Needs**: All categories (doctrine, threats, assets, missions, spectrum)

#### Agent 4: ATO Producer Agent
- **Active Phases**: Phase 4 (ATO Production)
- **Role**: Integrates EMS into Air Tasking Order
- **Responsibilities**:
  - Collect EMS mission plans
  - Integrate with kinetic strike packages
  - Generate SPINS annex (EMS special instructions)
  - Validate ATO completeness
- **Access Level**: SENSITIVE
- **Information Needs**: Doctrine, mission plans, spectrum allocations, asset status

#### Agent 5: Assessment Agent
- **Active Phases**: Phase 6 (Assessment)
- **Role**: Assesses effectiveness and generates lessons learned
- **Responsibilities**:
  - Collect execution data
  - Assess mission effectiveness
  - Analyze process improvement flags
  - Generate lessons learned
  - Update CKB with learnings
- **Access Level**: OPERATIONAL
- **Information Needs**: Doctrine, mission plans, process metrics, organizational data

### 3. Process Improvement Subsystem (Option C Feature)

**Critical Innovation**: Agents follow doctrine exactly BUT maintain a process improvement log.

**Inefficiency Types**:
1. `REDUNDANT_COORDINATION` - Multiple approvals for same thing
2. `INFORMATION_GAP` - Agent needs data not available
3. `TIMING_CONSTRAINT` - Doctrine timeline unrealistic
4. `DOCTRINE_CONTRADICTION` - Conflicting guidance
5. `AUTOMATION_OPPORTUNITY` - Manual process could be automated
6. `DECONFLICTION_ISSUE` - Spectrum conflicts recurring
7. `RESOURCE_BOTTLENECK` - Insufficient assets/time

**Workflow**:
- Agent executes procedure per doctrine
- If execution time > 1.3x expected → flag `TIMING_CONSTRAINT`
- If information unavailable → flag `INFORMATION_GAP`
- If manual coordination excessive → flag `AUTOMATION_OPPORTUNITY`
- System aggregates flags and identifies patterns
- Generates recommendations for process improvement

### 4. Technology Stack

```
Core Framework:
- Python 3.11+
- asyncio for concurrent agent operations

LLMs:
- Anthropic Claude Sonnet 4.5 (primary)
- OpenAI GPT-4 (alternative)
- Google Gemini Pro (alternative)

Vector Database:
- ChromaDB for doctrine knowledge base

Databases:
- MongoDB for operational data (threats, assets, spectrum, missions)

Authorization:
- Open Policy Agent (OPA) with Rego policies

API Framework:
- FastAPI for APIs
- Pydantic for data validation

MCP (Model Context Protocol):
- MCP servers for tool integration
- Standard protocol for AI-system integration

Geospatial:
- Shapely for geographic operations
- GeoJSON for area definitions
```

### 5. ATO Cycle Phases & Timing

```yaml
Total Cycle: 72 hours

Phase 1 - Objectives, Effects, Guidance (OEG):
  Duration: 6 hours
  Offset: 0 hours
  Active Agents: [ems_strategy_agent]
  Key Outputs: [ems_strategy, commander_guidance]

Phase 2 - Target Development:
  Duration: 8 hours
  Offset: 6 hours
  Active Agents: [ems_strategy_agent]
  Key Outputs: [target_list, ems_requirements]

Phase 3 - Weaponeering & Allocation:
  Duration: 10 hours
  Offset: 14 hours
  Active Agents: [ew_planner_agent, spectrum_manager_agent]
  Key Outputs: [ew_missions, frequency_allocations]
  Critical: true

Phase 4 - ATO Production:
  Duration: 6 hours
  Offset: 24 hours
  Active Agents: [ato_producer_agent, spectrum_manager_agent]
  Key Outputs: [ato_document, spins_annex]
  Critical: true

Phase 5 - Execution:
  Duration: 24 hours
  Offset: 30 hours
  Active Agents: [spectrum_manager_agent]
  Key Outputs: [execution_data, real_time_adjustments]

Phase 6 - Assessment:
  Duration: 18 hours
  Offset: 54 hours
  Active Agents: [assessment_agent]
  Key Outputs: [effectiveness_assessment, lessons_learned]
```

### 6. Access Control Model

```python
# Access Levels (NOT DoD classification)
PUBLIC = 1       # Publicly available
INTERNAL = 2     # Internal org use
OPERATIONAL = 3  # Operational personnel
SENSITIVE = 4    # Restricted operational
CRITICAL = 5     # Mission-critical

# Information Categories
- DOCTRINE: Published doctrine (PUBLIC/INTERNAL)
- THREAT_DATA: Threat intelligence (OPERATIONAL/SENSITIVE)
- ASSET_STATUS: Platform availability (OPERATIONAL)
- SPECTRUM_ALLOCATION: Frequency assignments (OPERATIONAL/SENSITIVE)
- MISSION_PLAN: Mission details (SENSITIVE/CRITICAL)
- ORGANIZATIONAL: Org structure, contacts (INTERNAL)
- PROCESS_METRICS: Performance data (INTERNAL/OPERATIONAL)

# Access Policies
Each category has:
- minimum_access_level
- additional_constraints (need_to_know, phase_restricted)
- sanitization_required (bool)
- audit_required (bool)
```

### 7. MCP Servers (4 Required)

#### MCP Server 1: Doctrine Query
```
Tools:
- query_doctrine(query, filters, top_k)
- get_procedure(procedure_name)
- check_doctrine_compliance(action_description)

Data Source: ChromaDB vector store of USAF doctrine
```

#### MCP Server 2: Spectrum Database
```
Tools:
- check_spectrum_conflicts(frequency_range, time_window, geographic_area)
- create_spectrum_allocation(...)
- query_allocations(filters)
- find_available_frequencies(...)

Data Source: MongoDB spectrum_management.allocations
```

#### MCP Server 3: Threat Intelligence
```
Tools:
- query_ems_threats(geographic_area, threat_types, access_level)
- get_threat_frequencies(threat_ids, access_level)

Data Source: MongoDB threat_intelligence.ems_threats
Access Control: Sanitize based on requester's access_level
```

#### MCP Server 4: Asset Tracking
```
Tools:
- query_ems_asset_availability(asset_types, time_window, capabilities)
- get_ems_asset_capabilities(asset_id)
- reserve_asset(asset_id, mission_id, time_window)

Data Source: MongoDB asset_management.ems_assets
```

### 8. OPA Authorization Policies

Key authorization rules (in Rego):

```rego
# Spectrum Manager can allocate frequencies during Phase 3
allow_frequency_allocation {
    input.agent.role == "spectrum_manager"
    input.ato_cycle.current_phase == "PHASE3_WEAPONEERING"
    input.action.type == "allocate_frequency"
    no_conflicts(input.action.frequency_range, input.action.time_window)
    within_authorized_band(input.action.frequency_range)
}

# Emergency reallocation during execution requires senior approval
allow_emergency_reallocation {
    input.ato_cycle.current_phase == "PHASE5_EXECUTION"
    input.action.type == "reallocate_frequency"
    input.action.reason == "emergency"
    input.action.approved_by_rank >= "O-5"
}

# EW Planner can assign assets during Phase 3
allow_asset_assignment {
    input.agent.role == "ew_planner"
    input.ato_cycle.current_phase == "PHASE3_WEAPONEERING"
    input.action.type == "assign_ems_asset"
    asset_available(input.action.asset_id, input.action.mission_window)
}
```

### 9. Example Workflows

#### Workflow 1: Frequency Allocation
```
1. EW Planner creates mission plan
2. EW Planner requests frequency from Spectrum Manager (via Aether OS)
3. Spectrum Manager checks conflicts (MCP: spectrum_server)
4. If conflicts found:
   a. Coordinate with conflicting users (per doctrine)
   b. Flag if coordination excessive (process improvement)
5. Check authorization (OPA policy + phase check)
6. Create allocation in database
7. Track execution time
8. If > 1.5x expected → flag TIMING_CONSTRAINT
```

#### Workflow 2: Process Improvement
```
1. Agent executes doctrinal procedure
2. Tracks execution time, information gaps, coordination steps
3. If inefficiency detected → call improvement_logger.flag_inefficiency()
4. Flag stored with context (ATO cycle, phase, workflow, time wasted)
5. Assessment Agent analyzes patterns at end of cycle
6. Identifies recurring issues (e.g., same workflow flagged 5+ times)
7. Generates recommendations (automate, streamline, grant access)
8. Human reviews and decides on implementation
```

## Directory Structure to Create

```
aether-os-usaf-ems/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── setup.py
│
├── aether_os/                    # Core framework
│   ├── __init__.py
│   ├── core.py                   # Main AetherOS class
│   ├── access_control.py         # Access levels, policies, profiles
│   ├── authorization.py          # Multi-factor authorization engine
│   ├── information_broker.py     # Information access with sanitization
│   ├── process_improvement.py    # Inefficiency tracking (Option C)
│   ├── orchestrator.py           # ATO cycle orchestration
│   └── doctrine_kb.py            # Doctrine knowledge base interface
│
├── agents/                       # AOC agents
│   ├── __init__.py
│   ├── base_agent.py             # Base class with common functionality
│   ├── ems_strategy_agent.py     # Phase 1-2
│   ├── spectrum_manager_agent.py # Phase 3, 5
│   ├── ew_planner_agent.py       # Phase 3
│   ├── ato_producer_agent.py     # Phase 4
│   └── assessment_agent.py       # Phase 6
│
├── mcp_servers/                  # MCP tool servers
│   ├── __init__.py
│   ├── doctrine_server.py        # Doctrine query MCP server
│   ├── spectrum_server.py        # Spectrum database MCP server
│   ├── threat_intel_server.py    # Threat intelligence MCP server
│   └── asset_tracking_server.py  # Asset availability MCP server
│
├── policies/                     # OPA policies
│   ├── README.md
│   ├── agent_authorization.rego  # Main authorization policy
│   ├── phase_constraints.rego    # Phase-based restrictions
│   └── test_policies.rego        # Policy tests
│
├── doctrine_kb/                  # Doctrine knowledge base
│   ├── README.md
│   ├── raw/                      # Original doctrine docs
│   ├── processed/                # Processed/chunked text
│   ├── chroma_db/                # Vector database
│   └── metadata/                 # Document metadata
│
├── scenarios/                    # Test scenarios
│   ├── README.md
│   ├── scenario_1_a2ad.yaml      # A2/AD challenge
│   ├── scenario_2_dynamic.yaml   # Dynamic retasking
│   └── scenario_3_coalition.yaml # Coalition coordination
│
├── config/                       # Configuration
│   ├── agent_profiles.yaml       # Agent access profiles
│   ├── access_policies.yaml      # Access control policies
│   └── ato_schedule.yaml         # ATO cycle timing
│
├── scripts/                      # Utility scripts
│   ├── __init__.py
│   ├── init_doctrine_kb.py       # Initialize doctrine KB
│   ├── run_ato_cycle.py          # Run ATO cycle simulation
│   ├── seed_test_data.py         # Populate test databases
│   └── evaluate_agents.py        # Run evaluation suite
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_authorization.py
│   ├── test_access_control.py
│   ├── test_agents.py
│   ├── test_orchestrator.py
│   ├── test_improvement_logger.py
│   └── test_integration.py
│
├── examples/                     # Usage examples
│   ├── README.md
│   ├── simple_query.py
│   ├── agent_interaction.py
│   └── process_improvement_demo.py
│
└── docs/                         # Documentation
    ├── architecture.md
    ├── agent_guide.md
    ├── deployment.md
    └── api_reference.md
```

## Implementation Instructions for Claude Code

### Priority 1: Core Framework (Critical Path)

1. **aether_os/access_control.py**
   - Implement AccessLevel enum, InformationCategory enum
   - Create AgentAccessProfile dataclass
   - Define ACCESS_POLICIES dict
   - Define AGENT_PROFILES dict (5 agents)
   - Implement check_access() function

2. **aether_os/authorization.py**
   - Create AOCAuthorizationContext class
   - Implement can_agent_act() with 6 checks:
     - Role authority
     - Phase appropriateness
     - Information access
     - Delegation chain
     - Doctrinal compliance
     - OPA policy evaluation
   - Implement OPA integration (POST to OPA server)

3. **aether_os/information_broker.py**
   - Create AOCInformationBroker class
   - Implement query() method with routing
   - Implement _query_doctrine(), _query_threats(), _query_spectrum(), etc.
   - Implement _sanitize_threat_data() and _sanitize_mission_data()
   - Implement audit logging

4. **aether_os/process_improvement.py**
   - Create InefficencyType enum (7 types)
   - Create ProcessImprovementFlag dataclass
   - Implement ProcessImprovementLogger class
   - Implement flag_inefficiency() method
   - Implement analyze_patterns() method
   - Implement _identify_patterns() and _generate_recommendations()

5. **aether_os/orchestrator.py**
   - Create ATOPhase enum
   - Create ATOCycleOrchestrator class
   - Implement _define_phase_schedule() (6 phases with timing)
   - Implement start_new_cycle(), get_current_phase()
   - Implement phase transition logic
   - Implement async _monitor_cycle() background task

6. **aether_os/doctrine_kb.py**
   - Create DoctrineKnowledgeBase class
   - Implement query() method (ChromaDB integration)
   - Implement get_procedure() method

7. **aether_os/core.py**
   - Create main AetherOS class
   - Initialize all subsystems (doctrine_kb, authorization, info_broker, improvement_logger, orchestrator)
   - Implement register_agent(), activate_agent(), deactivate_agent()
   - Implement send_agent_message() and broadcast_to_agents()
   - Implement query_information() and authorize_action()

### Priority 2: Agents

1. **agents/base_agent.py**
   - Create BaseAetherAgent abstract base class
   - Implement execute_doctrinal_procedure() with timing tracking
   - Implement escalate_for_human_decision()
   - Implement handle_event()

2. **agents/ems_strategy_agent.py**
   - Inherit from BaseAetherAgent
   - Implement develop_ems_strategy()
   - Implement _validate_against_doctrine()
   - Implement _identify_strategy_gaps()
   - Use LLM for strategy generation (grounded in doctrine)

3. **agents/spectrum_manager_agent.py**
   - Implement process_frequency_request()
   - Implement coordinate_deconfliction()
   - Implement emergency_reallocation()
   - Flag inefficiencies when coordination excessive

4. **agents/ew_planner_agent.py**
   - Implement plan_ew_missions()
   - Implement _request_frequency_allocation() (inter-agent communication)
   - Implement _check_ea_sigint_fratricide()
   - Generate missions using LLM grounded in doctrine

5. **agents/ato_producer_agent.py**
   - Implement produce_ato_ems_annex()
   - Implement _validate_mission_approvals()
   - Implement _integrate_ems_with_strikes()
   - Flag timing mismatches

6. **agents/assessment_agent.py**
   - Implement assess_ato_cycle()
   - Implement _analyze_doctrine_effectiveness() (Option C feature)
   - Call improvement_logger.analyze_patterns()
   - Generate lessons learned report

### Priority 3: MCP Servers

Implement each as standalone MCP server using `mcp.server` package:

1. **mcp_servers/doctrine_server.py**
   - Tools: query_doctrine, get_procedure, check_doctrine_compliance
   - Connect to ChromaDB
   - Use LLM for compliance checking

2. **mcp_servers/spectrum_server.py**
   - Tools: check_spectrum_conflicts, create_spectrum_allocation, find_available_frequencies
   - Connect to MongoDB
   - Implement frequency overlap detection

3. **mcp_servers/threat_intel_server.py**
   - Tools: query_ems_threats, get_threat_frequencies
   - Apply access-level-based sanitization
   - GeoJSON geographic queries

4. **mcp_servers/asset_tracking_server.py**
   - Tools: query_ems_asset_availability, get_ems_asset_capabilities
   - Check asset taskings for availability

### Priority 4: OPA Policies

Create in Rego language:

1. **policies/agent_authorization.rego**
   - Implement allow_frequency_allocation rule
   - Implement allow_asset_assignment rule
   - Implement allow_ato_approval rule
   - Implement allow_emergency_reallocation rule
   - Helper functions: no_conflicts, within_authorized_band, asset_available

2. **policies/phase_constraints.rego**
   - Implement phase-based access restrictions
   - Implement phase transition rules

### Priority 5: Scripts & Configuration

1. **scripts/init_doctrine_kb.py**
   - Scan doctrine_kb/raw/ directory
   - Process PDFs/documents
   - Chunk by section
   - Generate embeddings
   - Store in ChromaDB

2. **scripts/seed_test_data.py**
   - Create sample threat data in MongoDB
   - Create sample asset data
   - Create sample spectrum allocations
   - Insert sample doctrine procedures

3. **scripts/run_ato_cycle.py**
   - Initialize AetherOS
   - Register all 5 agents
   - Start ATO cycle
   - Run through all 6 phases
   - Generate final report

4. **scripts/evaluate_agents.py**
   - Load test scenarios
   - Run agents on scenarios
   - Score performance
   - Generate evaluation report

5. **Configuration files**
   - config/agent_profiles.yaml
   - config/access_policies.yaml
   - config/ato_schedule.yaml

### Priority 6: Supporting Files

1. **README.md** - Comprehensive project documentation
2. **requirements.txt** - All dependencies
3. **.env.example** - Configuration template
4. **setup.py** - Package setup
5. **.gitignore** - Ignore patterns

## Code Quality Requirements

### Must Have:
- Type hints on all functions
- Docstrings (Google style) on all classes and public methods
- Error handling with try/except where appropriate
- Logging with Python logging module
- Input validation with Pydantic where appropriate

### Code Style:
- Follow PEP 8
- Use dataclasses for data structures
- Use enums for constants
- Use async/await for concurrent operations
- Keep functions focused (single responsibility)

### Testing:
- Unit tests for each core component
- Integration tests for agent workflows
- Mock external dependencies (MongoDB, OPA, LLMs)

## Special Implementation Notes

### Process Improvement Integration:
Every agent method that executes doctrine should wrap execution in timing tracking:
```python
start_time = datetime.now()
result = execute_procedure()
execution_time = (datetime.now() - start_time).total_seconds() / 3600

if execution_time > expected_time * 1.5:
    self.improvement_logger.flag_inefficiency(...)
```

### LLM Integration:
Use Anthropic Claude Sonnet 4.5 by default:
```python
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4000,
    messages=[{"role": "user", "content": prompt}]
)
```

### MongoDB Schemas:
Define clear schemas for:
- threats: {_id, threat_type, location (GeoJSON), frequency_bands, classification, ...}
- assets: {_id, platform, asset_type, capabilities, status, ...}
- allocations: {_id, frequency_min_mhz, frequency_max_mhz, start_time, end_time, geographic_area, ...}

### ChromaDB Structure:
```python
collection.add(
    documents=[chunk_text],
    metadatas=[{
        "document": "AFI 10-703",
        "section": "4.3.2",
        "authority_level": "Service",
        "content_type": "procedure",
        "applicable_roles": ["ew_planner", "spectrum_manager"]
    }],
    ids=[chunk_id]
)
```

## Success Criteria

The prototype is successful if:

1. ✅ All 5 agents can be instantiated and registered
2. ✅ ATO cycle orchestrator can run through all 6 phases
3. ✅ Agents are activated/deactivated based on phase
4. ✅ Authorization checks work (role + phase + access level)
5. ✅ Information broker returns sanitized data based on access level
6. ✅ Process improvement flags are generated during agent execution
7. ✅ Pattern analysis identifies recurring inefficiencies
8. ✅ At least one complete workflow executes end-to-end (e.g., frequency allocation)
9. ✅ MCP servers respond to tool calls
10. ✅ Can run scripts/run_ato_cycle.py and see agents coordinate

## Generate This Project Now

Create the complete Aether OS prototype with all files, following this specification exactly. Ensure all imports work, all cross-references are correct, and the project is ready to run after:

```bash
cd aether-os-usaf-ems
pip install -r requirements.txt
cp .env.example .env
# Edit .env with API keys
python scripts/seed_test_data.py
python scripts/run_ato_cycle.py
```
