"""
Access control system for Aether OS.

Implements organizational access levels (NOT DoD classification) and information
category-based access control for AOC agents.
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Set, Optional
import logging

logger = logging.getLogger(__name__)


class AccessLevel(IntEnum):
    """Organizational access levels (NOT DoD classification)."""
    PUBLIC = 1       # Publicly available information
    INTERNAL = 2     # Internal organizational use
    OPERATIONAL = 3  # Operational personnel
    SENSITIVE = 4    # Restricted operational information
    CRITICAL = 5     # Mission-critical information


class InformationCategory(IntEnum):
    """Categories of information managed by Aether OS."""
    DOCTRINE = 1              # Published doctrine and procedures
    THREAT_DATA = 2           # Threat intelligence
    ASSET_STATUS = 3          # Platform and asset availability
    SPECTRUM_ALLOCATION = 4   # Frequency assignments
    MISSION_PLAN = 5          # Mission details and plans
    ORGANIZATIONAL = 6        # Organizational structure and contacts
    PROCESS_METRICS = 7       # Performance and process data


@dataclass
class InformationAccessPolicy:
    """Access policy for a specific information category."""
    category: InformationCategory
    minimum_access_level: AccessLevel
    need_to_know_required: bool = False
    phase_restricted: bool = False
    allowed_phases: Set[str] = field(default_factory=set)
    sanitization_required: bool = False
    audit_required: bool = True


@dataclass
class AgentAccessProfile:
    """Access profile defining an agent's permissions."""
    agent_id: str
    role: str
    access_level: AccessLevel
    authorized_categories: Set[InformationCategory]
    authorized_actions: Set[str]
    active_phases: Set[str]
    delegation_authority: bool = False
    max_delegation_level: AccessLevel = AccessLevel.INTERNAL


# Access policies for each information category
ACCESS_POLICIES = {
    InformationCategory.DOCTRINE: InformationAccessPolicy(
        category=InformationCategory.DOCTRINE,
        minimum_access_level=AccessLevel.PUBLIC,
        need_to_know_required=False,
        sanitization_required=False,
        audit_required=False,
    ),
    InformationCategory.THREAT_DATA: InformationAccessPolicy(
        category=InformationCategory.THREAT_DATA,
        minimum_access_level=AccessLevel.OPERATIONAL,
        need_to_know_required=True,
        sanitization_required=True,
        audit_required=True,
    ),
    InformationCategory.ASSET_STATUS: InformationAccessPolicy(
        category=InformationCategory.ASSET_STATUS,
        minimum_access_level=AccessLevel.OPERATIONAL,
        need_to_know_required=False,
        sanitization_required=False,
        audit_required=True,
    ),
    InformationCategory.SPECTRUM_ALLOCATION: InformationAccessPolicy(
        category=InformationCategory.SPECTRUM_ALLOCATION,
        minimum_access_level=AccessLevel.OPERATIONAL,
        need_to_know_required=True,
        sanitization_required=False,
        audit_required=True,
    ),
    InformationCategory.MISSION_PLAN: InformationAccessPolicy(
        category=InformationCategory.MISSION_PLAN,
        minimum_access_level=AccessLevel.SENSITIVE,
        need_to_know_required=True,
        sanitization_required=True,
        audit_required=True,
    ),
    InformationCategory.ORGANIZATIONAL: InformationAccessPolicy(
        category=InformationCategory.ORGANIZATIONAL,
        minimum_access_level=AccessLevel.INTERNAL,
        need_to_know_required=False,
        sanitization_required=False,
        audit_required=False,
    ),
    InformationCategory.PROCESS_METRICS: InformationAccessPolicy(
        category=InformationCategory.PROCESS_METRICS,
        minimum_access_level=AccessLevel.INTERNAL,
        need_to_know_required=False,
        sanitization_required=False,
        audit_required=True,
    ),
}


# Agent access profiles for the 5 AOC agents
AGENT_PROFILES = {
    "ems_strategy_agent": AgentAccessProfile(
        agent_id="ems_strategy_agent",
        role="ems_strategy",
        access_level=AccessLevel.SENSITIVE,
        authorized_categories={
            InformationCategory.DOCTRINE,
            InformationCategory.THREAT_DATA,
            InformationCategory.ORGANIZATIONAL,
            InformationCategory.PROCESS_METRICS,
        },
        authorized_actions={
            "query_doctrine",
            "query_threats",
            "develop_strategy",
            "request_information",
        },
        active_phases={"PHASE1_OEG", "PHASE2_TARGET_DEVELOPMENT"},
        delegation_authority=False,
    ),
    "spectrum_manager_agent": AgentAccessProfile(
        agent_id="spectrum_manager_agent",
        role="spectrum_manager",
        access_level=AccessLevel.OPERATIONAL,
        authorized_categories={
            InformationCategory.DOCTRINE,
            InformationCategory.SPECTRUM_ALLOCATION,
            InformationCategory.ASSET_STATUS,
            InformationCategory.THREAT_DATA,
        },
        authorized_actions={
            "query_doctrine",
            "allocate_frequency",
            "check_spectrum_conflicts",
            "coordinate_deconfliction",
            "emergency_reallocation",
            "query_assets",
        },
        active_phases={"PHASE3_WEAPONEERING", "PHASE5_EXECUTION"},
        delegation_authority=True,
        max_delegation_level=AccessLevel.OPERATIONAL,
    ),
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
            "query_doctrine",
            "query_threats",
            "query_assets",
            "plan_ew_missions",
            "request_frequency_allocation",
            "assign_ems_asset",
            "check_fratricide",
        },
        active_phases={"PHASE3_WEAPONEERING"},
        delegation_authority=False,
    ),
    "ato_producer_agent": AgentAccessProfile(
        agent_id="ato_producer_agent",
        role="ato_producer",
        access_level=AccessLevel.SENSITIVE,
        authorized_categories={
            InformationCategory.DOCTRINE,
            InformationCategory.MISSION_PLAN,
            InformationCategory.SPECTRUM_ALLOCATION,
            InformationCategory.ASSET_STATUS,
        },
        authorized_actions={
            "query_doctrine",
            "produce_ato_ems_annex",
            "validate_mission_approvals",
            "integrate_ems_with_strikes",
        },
        active_phases={"PHASE4_ATO_PRODUCTION"},
        delegation_authority=False,
    ),
    "assessment_agent": AgentAccessProfile(
        agent_id="assessment_agent",
        role="assessment",
        access_level=AccessLevel.OPERATIONAL,
        authorized_categories={
            InformationCategory.DOCTRINE,
            InformationCategory.MISSION_PLAN,
            InformationCategory.PROCESS_METRICS,
            InformationCategory.ORGANIZATIONAL,
        },
        authorized_actions={
            "query_doctrine",
            "assess_ato_cycle",
            "analyze_doctrine_effectiveness",
            "generate_lessons_learned",
            "query_process_metrics",
        },
        active_phases={"PHASE6_ASSESSMENT"},
        delegation_authority=False,
    ),
    "evaluator_agent": AgentAccessProfile(
        agent_id="evaluator_agent",
        role="evaluator",
        access_level=AccessLevel.SENSITIVE,
        authorized_categories={
            InformationCategory.DOCTRINE,
            InformationCategory.THREAT_DATA,
            InformationCategory.ASSET_STATUS,
            InformationCategory.MISSION_PLAN,
            InformationCategory.SPECTRUM_ALLOCATION,
            InformationCategory.PROCESS_METRICS,
            InformationCategory.ORGANIZATIONAL,
        },
        authorized_actions={
            "evaluate_agent_responses",
            "score_performance",
            "provide_feedback",
            "query_doctrine",
        },
        active_phases=set(),  # No phase restrictions - can evaluate at any time
        delegation_authority=False,
    ),
}


def check_access(
    agent_profile: AgentAccessProfile,
    category: InformationCategory,
    current_phase: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Check if an agent has access to a specific information category.

    Args:
        agent_profile: The agent's access profile
        category: The information category being accessed
        current_phase: Current ATO cycle phase (optional)

    Returns:
        Tuple of (access_granted: bool, denial_reason: Optional[str])
    """
    # Check if category is in agent's authorized categories
    if category not in agent_profile.authorized_categories:
        return False, f"Category {category.name} not in authorized categories"

    # Get the access policy for this category
    policy = ACCESS_POLICIES.get(category)
    if not policy:
        return False, f"No access policy defined for category {category.name}"

    # Check access level
    if agent_profile.access_level < policy.minimum_access_level:
        return False, f"Insufficient access level (required: {policy.minimum_access_level.name})"

    # Check phase restrictions
    if policy.phase_restricted and current_phase:
        if current_phase not in policy.allowed_phases:
            return False, f"Access not allowed in phase {current_phase}"

    # If we got here, access is granted
    logger.info(
        f"Access granted: agent={agent_profile.agent_id}, "
        f"category={category.name}, phase={current_phase}"
    )
    return True, None


def check_action_authorization(
    agent_profile: AgentAccessProfile,
    action: str,
    current_phase: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Check if an agent is authorized to perform a specific action.

    Args:
        agent_profile: The agent's access profile
        action: The action being attempted
        current_phase: Current ATO cycle phase (optional)

    Returns:
        Tuple of (authorized: bool, denial_reason: Optional[str])
    """
    # Check if action is in agent's authorized actions
    if action not in agent_profile.authorized_actions:
        return False, f"Action '{action}' not in authorized actions"

    # Check if agent is active in current phase
    if current_phase and current_phase not in agent_profile.active_phases:
        return False, f"Agent not active in phase {current_phase}"

    logger.info(
        f"Action authorized: agent={agent_profile.agent_id}, "
        f"action={action}, phase={current_phase}"
    )
    return True, None
