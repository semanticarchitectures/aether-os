# Agent Authorization Policies for Aether OS
#
# Defines authorization rules for agent actions based on role, phase,
# and specific action requirements.

package aether.agent_authorization

import rego.v1

# Default deny - all actions require explicit authorization
default allow := false

# Allow frequency allocation by Spectrum Manager in Phase 3
allow if {
    input.agent.role == "spectrum_manager"
    input.ato_cycle.current_phase == "PHASE3_WEAPONEERING"
    input.action.type == "allocate_frequency"
    no_conflicts
    within_authorized_band
}

# Allow emergency frequency reallocation during execution with approval
allow if {
    input.agent.role == "spectrum_manager"
    input.ato_cycle.current_phase == "PHASE5_EXECUTION"
    input.action.type == "reallocate_frequency"
    input.action.reason == "emergency"
    input.action.approved_by_rank >= "O-5"
}

# Allow EW Planner to assign assets during Phase 3
allow if {
    input.agent.role == "ew_planner"
    input.ato_cycle.current_phase == "PHASE3_WEAPONEERING"
    input.action.type == "assign_ems_asset"
    asset_available
}

# Allow ATO Producer to approve missions in Phase 4
allow if {
    input.agent.role == "ato_producer"
    input.ato_cycle.current_phase == "PHASE4_ATO_PRODUCTION"
    input.action.type == "approve_mission"
}

# Allow Assessment Agent to access process metrics in Phase 6
allow if {
    input.agent.role == "assessment"
    input.ato_cycle.current_phase == "PHASE6_ASSESSMENT"
    input.action.type == "query_process_metrics"
}

# Allow EMS Strategy Agent to develop strategy in Phase 1 or 2
allow if {
    input.agent.role == "ems_strategy"
    input.ato_cycle.current_phase in ["PHASE1_OEG", "PHASE2_TARGET_DEVELOPMENT"]
    input.action.type == "develop_strategy"
}

# Helper: Check for spectrum conflicts
no_conflicts if {
    # In production, would query spectrum database
    # For prototype, simplified check
    not input.action.has_conflicts
}

no_conflicts if {
    # If conflicts field not provided, assume no conflicts
    not input.action.has_conflicts
    not "has_conflicts" in object.keys(input.action)
}

# Helper: Check if frequency is within authorized band
within_authorized_band if {
    # Verify frequency range is within authorized spectrum
    freq_min := input.action.frequency_range[0]
    freq_max := input.action.frequency_range[1]

    # Example authorized bands (would be configurable)
    authorized_bands := [
        {"min": 2000.0, "max": 4000.0},  # S-band
        {"min": 4000.0, "max": 8000.0},  # C-band
        {"min": 8000.0, "max": 12000.0}, # X-band
    ]

    # Check if requested range falls within any authorized band
    some band in authorized_bands
    freq_min >= band.min
    freq_max <= band.max
}

within_authorized_band if {
    # If frequency_range not provided, allow (will be checked elsewhere)
    not input.action.frequency_range
}

# Helper: Check if asset is available
asset_available if {
    # In production, would query asset database
    # For prototype, assume available unless explicitly marked unavailable
    not input.action.asset_unavailable
}

# Helper: Get required access level for action type
required_access_level(action_type) := level if {
    access_requirements := {
        "allocate_frequency": 3,        # OPERATIONAL
        "assign_ems_asset": 4,           # SENSITIVE
        "approve_mission": 4,            # SENSITIVE
        "develop_strategy": 4,           # SENSITIVE
        "query_process_metrics": 2,     # INTERNAL
        "query_doctrine": 1,             # PUBLIC
    }
    level := access_requirements[action_type]
}

required_access_level(_) := 3  # Default to OPERATIONAL

# Check if agent has sufficient access level
sufficient_access_level if {
    required := required_access_level(input.action.type)
    input.agent.access_level >= required
}

# Deny reasons (for debugging)
deny_reasons contains reason if {
    not input.agent.role
    reason := "Missing agent role"
}

deny_reasons contains reason if {
    not input.ato_cycle.current_phase
    reason := "Missing ATO cycle phase"
}

deny_reasons contains reason if {
    not sufficient_access_level
    reason := sprintf(
        "Insufficient access level (required: %d, actual: %d)",
        [required_access_level(input.action.type), input.agent.access_level]
    )
}
