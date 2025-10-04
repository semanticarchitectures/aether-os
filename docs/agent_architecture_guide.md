# Aether OS Agent Architecture Guide

## Overview

The Aether OS agent architecture is designed around **5 specialized AOC (Air Operations Center) agents** that coordinate EMS (Electromagnetic Spectrum) operations through the 72-hour ATO (Air Tasking Order) cycle. Each agent has specific roles, access permissions, and activation phases.

## Architecture Layers

### 1. Base Agent Layer

**BaseAetherAgent** - Abstract base class providing core functionality:

```python
class BaseAetherAgent(ABC):
    """Abstract base class for all Aether OS agents."""
    
    def __init__(self, agent_id: str, aether_os: Any):
        self.agent_id = agent_id
        self.aether_os = aether_os
        self.profile = AGENT_PROFILES[agent_id]  # Access profile
        self.is_active = False
        self.current_context = None
```

**Core Capabilities:**
- ✅ **Doctrinal procedure execution** with timing tracking
- ✅ **Process improvement flagging** (Option C feature)
- ✅ **Context management** and semantic search
- ✅ **Inter-agent communication** via message passing
- ✅ **Access control** integration
- ✅ **Human escalation** for complex decisions

### 2. Concrete Agent Implementations

#### EMS Strategy Agent
- **Phases**: 1 (OEG), 2 (Target Development)
- **Role**: Develops EMS strategy from JFACC guidance
- **Access Level**: SENSITIVE (4)
- **Key Methods**: `develop_ems_strategy()`, `identify_ems_objectives()`

#### Spectrum Manager Agent  
- **Phases**: 3 (Weaponeering), 5 (Execution)
- **Role**: Manages frequency allocation and deconfliction
- **Access Level**: OPERATIONAL (3)
- **Key Methods**: `allocate_frequency()`, `coordinate_deconfliction()`, `emergency_reallocation()`

#### EW Planner Agent
- **Phases**: 3 (Weaponeering)
- **Role**: Plans Electronic Warfare missions
- **Access Level**: SENSITIVE (4)
- **Key Methods**: `plan_ew_missions()`, `assign_ems_assets()`, `check_ea_sigint_fratricide()`

#### ATO Producer Agent
- **Phases**: 4 (ATO Production)
- **Role**: Integrates EMS into Air Tasking Order
- **Access Level**: SENSITIVE (4)
- **Key Methods**: `produce_ato_ems_annex()`, `validate_mission_approvals()`

#### Assessment Agent
- **Phases**: 6 (Assessment)
- **Role**: Assesses effectiveness and generates lessons learned
- **Access Level**: OPERATIONAL (3)
- **Key Methods**: `assess_ato_cycle()`, `analyze_doctrine_effectiveness()`

### 3. Context-Aware Agents (LLM-Enhanced)

**ContextAwareBaseAgent** - Enhanced agents with LLM integration:

```python
class ContextAwareBaseAgent(BaseAetherAgent):
    """LLM-enhanced agent with structured reasoning."""
    
    def __init__(self, agent_id: str, aether_os: Any, llm_provider: LLMProvider):
        super().__init__(agent_id, aether_os)
        self.llm_client = LLMClient(primary_provider=llm_provider)
        self.semantic_tracker = SemanticContextTracker()
```

**Enhanced Capabilities:**
- 🧠 **LLM reasoning** (Claude Sonnet 4.5, GPT-4, Gemini)
- 📊 **Structured output parsing** with Pydantic models
- 🔍 **Semantic context tracking** for improved performance
- 📝 **Citation tracking** for doctrine references
- 🎯 **Confidence scoring** for decisions

## Agent Configuration System

### Access Control Configuration

Agents are configured through **two complementary systems**:

#### 1. YAML Configuration (`config/agent_profiles.yaml`)

```yaml
ew_planner_agent:
  role: ew_planner
  access_level: SENSITIVE  # 4
  authorized_categories:
    - DOCTRINE
    - THREAT_DATA
    - ASSET_STATUS
    - MISSION_PLAN
    - SPECTRUM_ALLOCATION
  authorized_actions:
    - query_doctrine
    - plan_ew_missions
    - request_frequency_allocation
    - assign_ems_asset
  active_phases:
    - PHASE3_WEAPONEERING
  delegation_authority: false
```

#### 2. Python Configuration (`aether_os/access_control.py`)

```python
AGENT_PROFILES = {
    "ew_planner_agent": AgentAccessProfile(
        agent_id="ew_planner_agent",
        role="ew_planner",
        access_level=AccessLevel.SENSITIVE,
        authorized_categories={
            InformationCategory.DOCTRINE,
            InformationCategory.THREAT_DATA,
            InformationCategory.ASSET_STATUS,
            InformationCategory.MISSION_PLAN,
            InformationCategory.SPECTRUM_ALLOCATION,
        },
        authorized_actions={
            "query_doctrine", "plan_ew_missions", 
            "request_frequency_allocation", "assign_ems_asset"
        },
        active_phases={ATOPhase.PHASE3_WEAPONEERING},
        delegation_authority=False,
    )
}
```

### Access Levels

```python
class AccessLevel(IntEnum):
    PUBLIC = 1       # Publicly available information
    INTERNAL = 2     # Internal organizational use
    OPERATIONAL = 3  # Operational personnel only
    SENSITIVE = 4    # Restricted operational data
    CRITICAL = 5     # Mission-critical information
```

### Information Categories

```python
class InformationCategory(Enum):
    DOCTRINE = "doctrine"                    # Published doctrine
    THREAT_DATA = "threat_data"             # Threat intelligence
    ASSET_STATUS = "asset_status"           # Platform availability
    SPECTRUM_ALLOCATION = "spectrum_allocation"  # Frequency assignments
    MISSION_PLAN = "mission_plan"           # Mission details
    ORGANIZATIONAL = "organizational"        # Org structure, contacts
    PROCESS_METRICS = "process_metrics"     # Performance data
```

## Agent Lifecycle Management

### 1. Registration and Initialization

```python
# Initialize Aether OS
aether_os = AetherOS()

# Create and register agents
ems_strategy = EMSStrategyAgent(aether_os)
ew_planner = EWPlannerAgent(aether_os)
spectrum_manager = SpectrumManagerAgent(aether_os)

aether_os.register_agent(ems_strategy)
aether_os.register_agent(ew_planner)
aether_os.register_agent(spectrum_manager)
```

### 2. Phase-Based Activation

```python
# ATO Cycle Orchestrator automatically activates agents by phase
orchestrator = ATOCycleOrchestrator()

# Phase 1: Only EMS Strategy Agent active
orchestrator.transition_to_phase("PHASE1_OEG")
# Activates: ems_strategy_agent

# Phase 3: EW Planner and Spectrum Manager active  
orchestrator.transition_to_phase("PHASE3_WEAPONEERING")
# Activates: ew_planner_agent, spectrum_manager_agent
# Deactivates: ems_strategy_agent
```

### 3. Task Execution

```python
# Agent executes phase-specific tasks
async def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
    if phase == "PHASE3_WEAPONEERING":
        # Execute doctrinal procedure with timing tracking
        missions = self.execute_doctrinal_procedure(
            procedure_name="Plan EW Missions",
            procedure_fn=self.plan_ew_missions,
            expected_time_hours=4.0,
            cycle_id=cycle_id,
            phase=phase,
        )
        return {"ew_missions": missions}
```

## Context Management

### Context Request Flow

```python
# 1. Agent requests context for specific task
context = agent.request_context(
    task_description="Plan EW missions for high-threat environment",
    max_context_size=16000
)

# 2. Context manager builds structured window
# - Doctrine: Relevant procedures and policies
# - Situational: Current threats, assets, spectrum
# - Historical: Past performance, lessons learned  
# - Collaborative: Other agents' outputs

# 3. Agent uses context and tracks references
agent.reference_context_item("doctrine_item_123")
agent.reference_context_item("threat_analysis_456")

# 4. Usage tracking for optimization
agent.finalize_context_usage(result)
```

### Context Structure

```python
@dataclass
class AgentContext:
    agent_id: str
    current_phase: ATOPhase
    current_task: Optional[str] = None
    
    # Context components
    doctrinal_context: DoctrineContext
    situational_context: SituationalContext  
    historical_context: HistoricalContext
    collaborative_context: CollaborativeContext
    
    # Usage tracking
    referenced_items: Set[str] = field(default_factory=set)
    utilization_rate: float = 0.0
```

## Inter-Agent Communication

### Message Passing System

```python
# Send message between agents
response = await aether_os.send_agent_message(
    from_agent="ew_planner_agent",
    to_agent="spectrum_manager_agent", 
    message_type="frequency_request",
    payload={
        "mission_id": "EA-ATO-001-001",
        "frequency_range": (2400.0, 2500.0),
        "time_window": ("2025-10-04T10:00:00Z", "2025-10-04T14:00:00Z"),
        "geographic_area": {...},
        "priority": "high"
    }
)
```

### Message Handler Dispatch

```python
class SpectrumManagerAgent(BaseAetherAgent):
    def _handle_frequency_request(self, from_agent: str, payload: Dict[str, Any]):
        """Handle frequency allocation request."""
        mission_id = payload["mission_id"]
        frequency_range = payload["frequency_range"]
        
        # Check for conflicts
        conflicts = self.check_spectrum_conflicts(frequency_range, ...)
        
        if not conflicts:
            allocation = self.allocate_frequency(payload)
            return {"success": True, "allocation": allocation}
        else:
            return {"success": False, "conflicts": conflicts}
```

## Process Improvement Tracking (Option C)

### Automatic Inefficiency Detection

```python
# Timing constraints
if execution_time > expected_time * 1.3:
    self.aether_os.improvement_logger.flag_inefficiency(
        ato_cycle_id=cycle_id,
        phase=phase,
        agent_id=self.agent_id,
        workflow_name=procedure_name,
        inefficiency_type=InefficencyType.TIMING_CONSTRAINT,
        description=f"Procedure took {execution_time:.2f}h vs expected {expected_time:.2f}h",
        time_wasted_hours=execution_time - expected_time,
        suggested_improvement="Adjust doctrine timeline or identify automation opportunities"
    )

# Information gaps
if required_data_unavailable:
    self.flag_information_gap(
        workflow_name="Plan EW Missions",
        missing_information="EMS requirements from Phase 2",
        cycle_id=cycle_id,
        phase=phase
    )
```

### Inefficiency Types Tracked

1. **REDUNDANT_COORDINATION** - Multiple approvals for same action
2. **INFORMATION_GAP** - Required data not available to agent
3. **TIMING_CONSTRAINT** - Doctrine timeline unrealistic
4. **DOCTRINE_CONTRADICTION** - Conflicting guidance
5. **AUTOMATION_OPPORTUNITY** - Manual process could be automated
6. **DECONFLICTION_ISSUE** - Spectrum conflicts recurring
7. **RESOURCE_BOTTLENECK** - Insufficient assets/time

## LLM Integration

### Structured Output with Pydantic

```python
class EWMissionPlanResponse(BaseModel):
    """Structured response for EW mission planning."""
    missions: List[MissionPlan] = Field(description="Planned EW missions")
    asset_assignments: Dict[str, str] = Field(description="Asset to target mapping")
    frequency_requests: List[str] = Field(description="Frequency allocation requests")
    context_citations: List[str] = Field(description="Context element IDs used")
    doctrine_citations: List[str] = Field(description="Specific doctrine references")
    information_gaps: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
```

### LLM Provider Configuration

```python
class LLMProvider(Enum):
    ANTHROPIC = "anthropic"  # Claude Sonnet 4.5 (primary)
    OPENAI = "openai"        # GPT-4 (fallback)
    GOOGLE = "google"        # Gemini Pro (fallback)

# Multi-provider client with automatic fallback
llm_client = LLMClient(
    primary_provider=LLMProvider.ANTHROPIC,
    max_retries=3,
    retry_delay=1.0
)
```

## Agent Access Control Matrix

| Agent | Access Level | Categories | Active Phases |
|-------|-------------|------------|---------------|
| EMS Strategy | SENSITIVE (4) | 4/7 categories | Phase 1-2 |
| Spectrum Manager | OPERATIONAL (3) | 4/7 categories | Phase 3, 5 |
| EW Planner | SENSITIVE (4) | 5/7 categories | Phase 3 |
| ATO Producer | SENSITIVE (4) | 4/7 categories | Phase 4 |
| Assessment | OPERATIONAL (3) | 4/7 categories | Phase 6 |

## Key Design Principles

### 1. **Modular Architecture**
- Base class provides common functionality
- Specialized implementations for specific roles
- Clear separation of concerns

### 2. **Configuration-Driven Access Control**
- YAML configuration for easy modification
- Python enforcement for security
- Multi-level authorization checks

### 3. **Phase-Based Lifecycle**
- Agents activate only when needed
- Automatic orchestration by ATO cycle
- Resource optimization

### 4. **Intelligent Context Management**
- Semantic search for relevant information
- Usage tracking for optimization
- Access control integration

### 5. **Built-in Process Improvement**
- Automatic inefficiency detection
- Pattern analysis across cycles
- Continuous optimization (Option C)

### 6. **Doctrinal Compliance**
- Agents follow USAF doctrine exactly
- Flag inefficiencies without breaking compliance
- Human escalation for complex decisions

## Example: Complete Agent Workflow

```python
# 1. Agent activation
orchestrator.transition_to_phase("PHASE3_WEAPONEERING")
# -> Activates ew_planner_agent, spectrum_manager_agent

# 2. Context request
context = ew_planner.request_context("Plan EW missions for A2/AD environment")

# 3. Doctrinal procedure execution
missions = ew_planner.execute_doctrinal_procedure(
    procedure_name="Plan EW Missions",
    procedure_fn=ew_planner.plan_ew_missions,
    expected_time_hours=4.0,
    cycle_id="ATO-001",
    phase="PHASE3_WEAPONEERING"
)

# 4. Inter-agent communication
for mission in missions:
    response = await aether_os.send_agent_message(
        from_agent="ew_planner_agent",
        to_agent="spectrum_manager_agent",
        message_type="frequency_request",
        payload=mission.frequency_request
    )

# 5. Process improvement tracking
# -> Automatic timing analysis
# -> Information gap detection
# -> Coordination efficiency monitoring

# 6. Context usage finalization
ew_planner.finalize_context_usage({"missions": missions})
```

This architecture provides a robust, scalable, and efficient system for AI-mediated EMS operations while maintaining strict doctrinal compliance and continuous process improvement.
