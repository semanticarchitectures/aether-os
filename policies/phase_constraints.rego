# Phase Constraint Policies for Aether OS
#
# Defines which agents can be active in which ATO cycle phases
# and enforces phase-based access restrictions.

package aether.phase_constraints

import rego.v1

# Define which agents are allowed in each phase
phase_active_agents := {
    "PHASE1_OEG": ["ems_strategy_agent"],
    "PHASE2_TARGET_DEVELOPMENT": ["ems_strategy_agent"],
    "PHASE3_WEAPONEERING": ["ew_planner_agent", "spectrum_manager_agent"],
    "PHASE4_ATO_PRODUCTION": ["ato_producer_agent", "spectrum_manager_agent"],
    "PHASE5_EXECUTION": ["spectrum_manager_agent"],
    "PHASE6_ASSESSMENT": ["assessment_agent"],
}

# Check if agent is allowed to be active in phase
agent_active_in_phase(agent_id, phase) if {
    allowed_agents := phase_active_agents[phase]
    agent_id in allowed_agents
}

# Check if phase transition is valid
valid_phase_transition(from_phase, to_phase) if {
    # Define valid phase transitions
    valid_transitions := {
        "PHASE1_OEG": ["PHASE2_TARGET_DEVELOPMENT"],
        "PHASE2_TARGET_DEVELOPMENT": ["PHASE3_WEAPONEERING"],
        "PHASE3_WEAPONEERING": ["PHASE4_ATO_PRODUCTION"],
        "PHASE4_ATO_PRODUCTION": ["PHASE5_EXECUTION"],
        "PHASE5_EXECUTION": ["PHASE6_ASSESSMENT"],
        "PHASE6_ASSESSMENT": ["PHASE1_OEG"],  # Cycle restart
    }

    allowed := valid_transitions[from_phase]
    to_phase in allowed
}

# Phase duration constraints (in hours)
phase_durations := {
    "PHASE1_OEG": 6,
    "PHASE2_TARGET_DEVELOPMENT": 8,
    "PHASE3_WEAPONEERING": 10,
    "PHASE4_ATO_PRODUCTION": 6,
    "PHASE5_EXECUTION": 24,
    "PHASE6_ASSESSMENT": 18,
}

# Get expected duration for phase
expected_duration(phase) := duration if {
    duration := phase_durations[phase]
}

expected_duration(_) := 0  # Unknown phase

# Check if phase is critical (cannot be skipped)
is_critical_phase(phase) if {
    phase in ["PHASE3_WEAPONEERING", "PHASE4_ATO_PRODUCTION"]
}

# Action restrictions by phase
phase_allowed_actions := {
    "PHASE1_OEG": [
        "develop_strategy",
        "query_doctrine",
        "query_threats",
    ],
    "PHASE2_TARGET_DEVELOPMENT": [
        "develop_strategy",
        "identify_requirements",
        "query_doctrine",
        "query_threats",
    ],
    "PHASE3_WEAPONEERING": [
        "plan_ew_missions",
        "allocate_frequency",
        "assign_ems_asset",
        "check_spectrum_conflicts",
        "query_doctrine",
        "query_threats",
        "query_assets",
    ],
    "PHASE4_ATO_PRODUCTION": [
        "produce_ato_ems_annex",
        "approve_mission",
        "validate_mission_approvals",
        "query_doctrine",
    ],
    "PHASE5_EXECUTION": [
        "monitor_execution",
        "reallocate_frequency",
        "emergency_reallocation",
    ],
    "PHASE6_ASSESSMENT": [
        "assess_ato_cycle",
        "analyze_doctrine_effectiveness",
        "query_process_metrics",
        "generate_lessons_learned",
    ],
}

# Check if action is allowed in phase
action_allowed_in_phase(action_type, phase) if {
    allowed_actions := phase_allowed_actions[phase]
    action_type in allowed_actions
}

# Information categories accessible by phase
phase_information_access := {
    "PHASE1_OEG": [
        "DOCTRINE",
        "THREAT_DATA",
        "ORGANIZATIONAL",
    ],
    "PHASE2_TARGET_DEVELOPMENT": [
        "DOCTRINE",
        "THREAT_DATA",
        "ORGANIZATIONAL",
    ],
    "PHASE3_WEAPONEERING": [
        "DOCTRINE",
        "THREAT_DATA",
        "ASSET_STATUS",
        "SPECTRUM_ALLOCATION",
        "MISSION_PLAN",
    ],
    "PHASE4_ATO_PRODUCTION": [
        "DOCTRINE",
        "MISSION_PLAN",
        "SPECTRUM_ALLOCATION",
        "ASSET_STATUS",
    ],
    "PHASE5_EXECUTION": [
        "SPECTRUM_ALLOCATION",
        "ASSET_STATUS",
        "MISSION_PLAN",
    ],
    "PHASE6_ASSESSMENT": [
        "DOCTRINE",
        "MISSION_PLAN",
        "PROCESS_METRICS",
        "ORGANIZATIONAL",
    ],
}

# Check if information category is accessible in phase
info_accessible_in_phase(category, phase) if {
    accessible := phase_information_access[phase]
    category in accessible
}
