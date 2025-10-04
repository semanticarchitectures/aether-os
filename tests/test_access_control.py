"""
Tests for access control system
"""

import pytest
from aether_os.access_control import (
    AccessLevel,
    InformationCategory,
    AGENT_PROFILES,
    check_access,
    check_action_authorization,
)


def test_agent_profiles_defined():
    """Test that all 5 agent profiles are defined."""
    expected_agents = [
        "ems_strategy_agent",
        "spectrum_manager_agent",
        "ew_planner_agent",
        "ato_producer_agent",
        "assessment_agent",
    ]

    for agent_id in expected_agents:
        assert agent_id in AGENT_PROFILES


def test_check_access_doctrine():
    """Test access to doctrine (public category)."""
    # All agents should have access to doctrine
    for agent_id, profile in AGENT_PROFILES.items():
        if InformationCategory.DOCTRINE in profile.authorized_categories:
            access_granted, reason = check_access(
                profile, InformationCategory.DOCTRINE
            )
            assert access_granted is True


def test_check_access_denied():
    """Test access denial for unauthorized category."""
    # EMS Strategy Agent should not have access to spectrum allocation
    ems_profile = AGENT_PROFILES["ems_strategy_agent"]

    access_granted, reason = check_access(
        ems_profile, InformationCategory.SPECTRUM_ALLOCATION
    )

    assert access_granted is False
    assert "not in authorized categories" in reason


def test_check_action_authorization():
    """Test action authorization."""
    spectrum_profile = AGENT_PROFILES["spectrum_manager_agent"]

    # Should be authorized for allocate_frequency
    authorized, reason = check_action_authorization(
        spectrum_profile, "allocate_frequency", "PHASE3_WEAPONEERING"
    )

    assert authorized is True


def test_check_action_wrong_phase():
    """Test action denial in wrong phase."""
    spectrum_profile = AGENT_PROFILES["spectrum_manager_agent"]

    # Should NOT be authorized in Phase 1
    authorized, reason = check_action_authorization(
        spectrum_profile, "allocate_frequency", "PHASE1_OEG"
    )

    assert authorized is False
    assert "not active in phase" in reason
