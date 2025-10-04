# Policy Tests for Aether OS
#
# Unit tests for authorization policies

package aether.agent_authorization

import rego.v1

# Test: Spectrum Manager can allocate frequency in Phase 3
test_spectrum_manager_phase3_allow if {
    allow with input as {
        "agent": {
            "role": "spectrum_manager",
            "access_level": 3,
        },
        "action": {
            "type": "allocate_frequency",
            "frequency_range": [2400.0, 2500.0],
        },
        "ato_cycle": {
            "current_phase": "PHASE3_WEAPONEERING",
        },
    }
}

# Test: Spectrum Manager cannot allocate in wrong phase
test_spectrum_manager_wrong_phase_deny if {
    not allow with input as {
        "agent": {
            "role": "spectrum_manager",
            "access_level": 3,
        },
        "action": {
            "type": "allocate_frequency",
            "frequency_range": [2400.0, 2500.0],
        },
        "ato_cycle": {
            "current_phase": "PHASE1_OEG",
        },
    }
}

# Test: EW Planner can assign assets in Phase 3
test_ew_planner_assign_asset_allow if {
    allow with input as {
        "agent": {
            "role": "ew_planner",
            "access_level": 4,
        },
        "action": {
            "type": "assign_ems_asset",
        },
        "ato_cycle": {
            "current_phase": "PHASE3_WEAPONEERING",
        },
    }
}

# Test: Emergency reallocation requires approval
test_emergency_reallocation_with_approval if {
    allow with input as {
        "agent": {
            "role": "spectrum_manager",
            "access_level": 3,
        },
        "action": {
            "type": "reallocate_frequency",
            "reason": "emergency",
            "approved_by_rank": "O-5",
        },
        "ato_cycle": {
            "current_phase": "PHASE5_EXECUTION",
        },
    }
}

# Test: Within authorized band
test_within_authorized_band if {
    within_authorized_band with input as {
        "action": {
            "frequency_range": [2400.0, 2500.0],  # Within S-band
        },
    }
}

# Test: Outside authorized band
test_outside_authorized_band if {
    not within_authorized_band with input as {
        "action": {
            "frequency_range": [15000.0, 16000.0],  # Outside defined bands
        },
    }
}
