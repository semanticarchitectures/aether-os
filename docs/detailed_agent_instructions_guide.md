# Detailed Agent Instructions Guide

## Overview

This guide explains how to provide comprehensive, detailed instructions to Aether OS agents for complex mission planning scenarios. The system supports multiple methods for instruction delivery, from simple task descriptions to complex multi-layered scenarios.

## Instruction Methods

### 1. **Direct Method Calls**

The most straightforward approach for specific tasks:

```python
# Simple mission planning
response = await ew_planner.plan_missions(
    mission_type="SEAD",
    targets=["SAM-001", "SAM-002"],
    timeframe="H-hour to H+4"
)

# Complex mission with detailed parameters
response = await ew_planner.plan_complex_missions(
    mission_instructions={
        "mission_type": "Multi-domain SEAD/EA",
        "threat_environment": detailed_threats,
        "available_assets": asset_inventory,
        "mission_objectives": objectives_dict,
        "constraints": constraints_dict,
        "coordination_requirements": coordination_dict
    },
    cycle_id="ATO-001"
)
```

### 2. **YAML Scenario Files**

For repeatable, complex scenarios:

```yaml
# scenarios/agent_tests/my_complex_mission.yaml
scenario_id: complex_mission_001
name: "Multi-Domain Operation"
agent_id: ew_planner_agent

context:
  phase: PHASE3_WEAPONEERING
  task_description: "Plan complex EW missions"
  
  threats:
    - threat_id: "SAM-001"
      threat_type: "S-400 Triumf"
      location: {lat: 36.0, lon: 44.0}
      # ... detailed threat parameters
  
  assets:
    - asset_id: "EA-001"
      platform: "EA-18G Growler"
      # ... detailed asset capabilities

messages:
  - message_type: "plan_complex_missions"
    payload:
      mission_type: "SEAD"
      # ... detailed mission parameters
```

### 3. **Structured Context Objects**

For programmatic scenario building:

```python
from aether_os.agent_context import AgentContext, SituationalContext

context = AgentContext(
    agent_id="ew_planner_agent",
    current_phase=ATOPhase.PHASE3_WEAPONEERING,
    situational_context=SituationalContext(
        current_threats=[
            {
                "threat_id": "SAM-001",
                "threat_type": "S-400",
                "location": {"lat": 36.0, "lon": 44.0},
                "priority": "critical",
                "capabilities": ["long-range", "multi-target"],
                "countermeasures": ["frequency-agile", "low-rcs-detection"]
            }
        ],
        available_assets=[
            {
                "asset_id": "EA-001",
                "platform": "EA-18G",
                "capabilities": ["stand-in-jamming", "harm-shooting"],
                "limitations": ["range-limited", "weather-dependent"]
            }
        ]
    )
)

# Provide context to agent
agent.current_context = context
```

## Instruction Components

### 1. **Mission Objectives**

Define clear, measurable objectives with priorities:

```python
mission_objectives = {
    "primary_objectives": [
        {
            "objective_id": "OBJ-001",
            "description": "Suppress S-400 system to enable strike package penetration",
            "priority": "critical",
            "success_criteria": "S-400 radar offline for minimum 30 minutes",
            "timeline": "H-hour to H+0:30",
            "coordination": "Must coordinate with Package Alpha TOT"
        }
    ],
    "secondary_objectives": [
        {
            "objective_id": "OBJ-002",
            "description": "Collect SIGINT on backup systems",
            "priority": "medium",
            "success_criteria": "Identify backup C2 frequencies",
            "timeline": "H-2:00 to H+4:00"
        }
    ],
    "force_protection": [
        {
            "objective_id": "FP-001",
            "description": "Protect friendly communications",
            "priority": "high",
            "success_criteria": "Maintain 90% friendly comms availability"
        }
    ]
}
```

### 2. **Threat Environment**

Provide comprehensive threat characterization:

```python
threat_environment = [
    {
        "threat_id": "IADS-001",
        "threat_type": "Integrated Air Defense System",
        "location": {"lat": 36.0, "lon": 44.0, "elevation": 150},
        "priority": "critical",
        "components": [
            {
                "component_id": "SAM-001",
                "type": "S-400 Triumf",
                "engagement_range_nm": 250,
                "frequency_bands": ["C-band", "S-band", "X-band"],
                "special_capabilities": ["Low-RCS detection", "Multi-target engagement"],
                "mobility": "semi-mobile",
                "operational_status": "active",
                "countermeasures": ["Frequency agility", "ECCM"]
            }
        ],
        "command_control": {
            "c2_node_id": "C2-001",
            "communication_links": ["VHF", "UHF", "SHF"],
            "backup_systems": True,
            "encryption": "military-grade"
        }
    }
]
```

### 3. **Asset Inventory**

Detail available assets with full capabilities:

```python
available_assets = [
    {
        "asset_id": "EA-001",
        "platform": "EA-18G Growler",
        "squadron": "VAQ-129",
        "capability": "Stand-in jamming",
        "availability": "available",
        "location": {"lat": 34.0, "lon": 42.0},
        "performance": {
            "effective_range_nm": 50,
            "frequency_coverage": "C-band through Ka-band",
            "jamming_power": "high",
            "survivability": "high",
            "mission_duration_hours": 4.5
        },
        "systems": {
            "coordination_systems": ["Link-16", "MIDS"],
            "weapons": ["AGM-88 HARM"],
            "sensors": ["ALQ-218 RWR", "ALQ-99 jammer"]
        },
        "special_capabilities": [
            "AESA radar jamming",
            "Communications disruption",
            "Threat geolocation"
        ],
        "limitations": [
            "Weather-dependent effectiveness",
            "Limited persistence",
            "Requires tanker support"
        ]
    }
]
```

### 4. **Constraints and Limitations**

Specify operational constraints:

```python
constraints = {
    "temporal_constraints": {
        "mission_window": "H-hour to H+4:00",
        "weather_window": "Clear conditions required H-0:30 to H+1:00",
        "coordination_deadlines": {
            "frequency_requests": "H-24:00",
            "airspace_coordination": "H-12:00",
            "final_mission_brief": "H-2:00"
        }
    },
    "geographic_constraints": {
        "no_fly_zones": [
            {"area": "Civilian airport", "coordinates": [[35.9, 43.7], [35.95, 43.75]]}
        ],
        "restricted_areas": [
            {"area": "Population center", "altitude_limit": 15000}
        ]
    },
    "spectrum_constraints": {
        "protected_frequencies": [
            {"band": "121.5 MHz", "purpose": "Emergency"},
            {"band": "243.0 MHz", "purpose": "Military emergency"}
        ],
        "coordination_required": [
            {"band": "VHF Air Traffic Control", "authority": "Host nation"}
        ]
    },
    "rules_of_engagement": {
        "jamming_restrictions": "No jamming of civilian communications",
        "kinetic_restrictions": "Weapons release only on confirmed military targets",
        "collateral_damage": "Minimize civilian impact"
    }
}
```

### 5. **Coordination Requirements**

Define inter-service and coalition coordination:

```python
coordination_requirements = {
    "strike_packages": [
        {
            "package_id": "PKG-ALPHA",
            "mission": "Primary target strike",
            "aircraft": ["F-35A x4", "F-16C x2"],
            "toa": "H+0:30",  # Time Over Target
            "target": "Command bunker",
            "ems_support_required": "SEAD escort, communications jamming",
            "coordination_frequency": "251.0 MHz"
        }
    ],
    "coalition_forces": [
        {
            "nation": "Partner Nation A",
            "assets": ["EF-2000 x2"],
            "role": "Air superiority",
            "coordination_freq": "251.0 MHz",
            "liaison": "AWACS Callsign Magic",
            "special_requirements": ["Frequency deconfliction", "IFF coordination"]
        }
    ],
    "supporting_elements": [
        {
            "element": "AWACS",
            "callsign": "Magic 01",
            "frequency": "251.0 MHz",
            "role": "Air battle management",
            "coverage_area": "AOR-ALPHA"
        }
    ]
}
```

## Advanced Instruction Techniques

### 1. **Layered Context Building**

Build context progressively for complex scenarios:

```python
# Start with basic context
basic_context = agent.request_context("Plan EW missions")

# Add detailed threat analysis
threat_context = build_threat_context(threat_environment)
agent.add_context_layer("threats", threat_context)

# Add asset capabilities
asset_context = build_asset_context(available_assets)
agent.add_context_layer("assets", asset_context)

# Add coordination requirements
coord_context = build_coordination_context(coordination_requirements)
agent.add_context_layer("coordination", coord_context)
```

### 2. **Template-Based Instructions**

Use structured templates for consistent instruction format:

```python
from aether_os.prompt_builder import get_task_template

# Use predefined templates
task = get_task_template(
    "plan_complex_missions",
    mission_type="Multi-domain SEAD",
    threat_summary="Layered A2/AD with S-400, S-300, Pantsir",
    asset_summary="EA-18G, EC-130H, F-16CJ available",
    timeline="H-hour to H+4:00",
    special_instructions="Coordinate with coalition partners"
)

# Custom template
custom_template = """
Plan ${mission_type} missions with the following parameters:

THREAT ENVIRONMENT:
${threat_details}

AVAILABLE ASSETS:
${asset_details}

MISSION OBJECTIVES:
${objectives}

CONSTRAINTS:
${constraints}

COORDINATION REQUIREMENTS:
${coordination}

SPECIAL INSTRUCTIONS:
${special_instructions}
"""
```

### 3. **Multi-Agent Coordination Instructions**

Coordinate multiple agents with shared instructions:

```python
# Shared mission context
shared_context = {
    "mission_id": "COMPLEX-001",
    "mission_type": "Multi-domain A2/AD penetration",
    "timeline": "H-hour to H+4:00",
    "threat_environment": threat_environment,
    "available_assets": available_assets
}

# Agent-specific instructions
ems_strategy_instructions = {
    **shared_context,
    "focus": "Develop overarching EMS strategy",
    "deliverables": ["EMS concept of operations", "Asset allocation guidance"]
}

ew_planner_instructions = {
    **shared_context,
    "focus": "Detailed mission planning",
    "deliverables": ["Mission plans", "Asset assignments", "Frequency requests"]
}

spectrum_manager_instructions = {
    **shared_context,
    "focus": "Frequency allocation and deconfliction",
    "deliverables": ["Frequency allocations", "Deconfliction plan"]
}
```

## Running Complex Scenarios

### 1. **Python Script Execution**

```bash
# Run complex mission planning example
python examples/complex_mission_planning.py

# Run with specific parameters
python examples/complex_mission_planning.py --scenario complex_a2ad --agents all
```

### 2. **YAML Scenario Execution**

```bash
# Run YAML scenario
python scripts/run_yaml_scenario.py scenarios/agent_tests/complex_multi_domain_mission.yaml

# Run with evaluation
python scripts/run_yaml_scenario.py scenarios/agent_tests/complex_multi_domain_mission.yaml --evaluate
```

### 3. **Interactive Testing**

```python
# Interactive agent testing
from scripts.test_agent import run_interactive_test

# Create test scenario
scenario = create_complex_scenario()

# Run interactive test
await run_interactive_test(
    agent_id="ew_planner_agent",
    scenario=scenario,
    interactive=True
)
```

## Best Practices

### 1. **Instruction Clarity**

- ✅ Use specific, measurable objectives
- ✅ Provide complete threat characterization
- ✅ Include all relevant constraints
- ✅ Specify coordination requirements
- ❌ Avoid vague or ambiguous instructions

### 2. **Context Optimization**

- ✅ Prioritize most relevant information
- ✅ Use structured data formats
- ✅ Include historical lessons learned
- ✅ Provide doctrinal guidance
- ❌ Don't overwhelm with unnecessary details

### 3. **Scenario Realism**

- ✅ Base scenarios on realistic threats
- ✅ Use accurate asset capabilities
- ✅ Include realistic constraints
- ✅ Consider coalition requirements
- ❌ Avoid unrealistic or impossible scenarios

### 4. **Evaluation Criteria**

- ✅ Define clear success metrics
- ✅ Include doctrine compliance checks
- ✅ Measure coordination effectiveness
- ✅ Assess adaptability and flexibility
- ❌ Don't rely solely on subjective evaluation

## Example Usage

```python
# Complete example of detailed agent instructions
async def run_complex_mission():
    # Initialize scenario
    scenario = ComplexMissionScenario()
    
    # Create detailed instructions
    instructions = {
        "mission_objectives": scenario.mission_objectives,
        "threat_environment": scenario.threat_environment,
        "available_assets": scenario.available_assets,
        "constraints": scenario.constraints,
        "coordination_requirements": scenario.coordination_requirements,
        "special_instructions": [
            "Prioritize S-400 suppression for strike package success",
            "Coordinate jamming timeline to avoid SIGINT fratricide",
            "Maintain continuous friendly communications protection",
            "Adapt to enemy countermeasures as needed"
        ]
    }
    
    # Execute mission planning
    response = await ew_planner.plan_complex_missions(
        mission_instructions=instructions,
        cycle_id="ATO-COMPLEX-001"
    )
    
    return response
```

This comprehensive approach enables agents to handle complex, realistic military scenarios with the detailed instructions necessary for effective mission planning and coordination.
