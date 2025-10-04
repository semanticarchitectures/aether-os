"""
Multi-factor authorization engine for Aether OS.

Implements 6-factor authorization checks:
1. Role authority
2. Phase appropriateness
3. Information access
4. Delegation chain
5. Doctrinal compliance
6. OPA policy evaluation
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
import os
import requests

from aether_os.access_control import (
    AgentAccessProfile,
    InformationCategory,
    check_access,
    check_action_authorization,
)
from aether_os.orchestrator import ATOPhase

logger = logging.getLogger(__name__)


@dataclass
class AOCAuthorizationContext:
    """Context for authorization decision."""
    agent_profile: AgentAccessProfile
    action: str
    current_phase: Optional[ATOPhase] = None
    information_category: Optional[InformationCategory] = None
    delegation_chain: list[str] = None
    additional_context: Dict[str, Any] = None

    def __post_init__(self):
        if self.delegation_chain is None:
            self.delegation_chain = []
        if self.additional_context is None:
            self.additional_context = {}


@dataclass
class AuthorizationDecision:
    """Result of an authorization check."""
    authorized: bool
    reason: str
    failed_checks: list[str] = None

    def __post_init__(self):
        if self.failed_checks is None:
            self.failed_checks = []


class AOCAuthorizationEngine:
    """
    Multi-factor authorization engine.

    Evaluates authorization requests using 6 different checks to ensure
    agents act within their authority and according to doctrine.
    """

    def __init__(self, opa_url: Optional[str] = None):
        """
        Initialize the authorization engine.

        Args:
            opa_url: URL of Open Policy Agent server (optional)
        """
        self.opa_url = opa_url or os.getenv("OPA_URL", "http://localhost:8181")
        logger.info(f"AOCAuthorizationEngine initialized (OPA: {self.opa_url})")

    def can_agent_act(self, context: AOCAuthorizationContext) -> AuthorizationDecision:
        """
        Determine if an agent can perform an action.

        Performs 6-factor authorization check:
        1. Role authority - Does agent's role allow this action?
        2. Phase appropriateness - Is agent active in current phase?
        3. Information access - Does agent have access to required info?
        4. Delegation chain - Is delegation valid?
        5. Doctrinal compliance - Does action comply with doctrine?
        6. OPA policy evaluation - Does OPA policy allow?

        Args:
            context: Authorization context

        Returns:
            AuthorizationDecision
        """
        failed_checks = []

        # Check 1: Role authority
        if not self._check_role_authority(context):
            failed_checks.append("role_authority")

        # Check 2: Phase appropriateness
        if not self._check_phase_appropriateness(context):
            failed_checks.append("phase_appropriateness")

        # Check 3: Information access (if applicable)
        if context.information_category:
            if not self._check_information_access(context):
                failed_checks.append("information_access")

        # Check 4: Delegation chain (if applicable)
        if context.delegation_chain:
            if not self._check_delegation_chain(context):
                failed_checks.append("delegation_chain")

        # Check 5: Doctrinal compliance
        # Note: This is a placeholder - would integrate with doctrine KB
        if not self._check_doctrinal_compliance(context):
            failed_checks.append("doctrinal_compliance")

        # Check 6: OPA policy evaluation
        if not self._check_opa_policy(context):
            failed_checks.append("opa_policy")

        # Make decision
        if failed_checks:
            return AuthorizationDecision(
                authorized=False,
                reason=f"Authorization denied: failed checks: {', '.join(failed_checks)}",
                failed_checks=failed_checks,
            )
        else:
            return AuthorizationDecision(
                authorized=True,
                reason="Authorization granted: all checks passed",
            )

    def _check_role_authority(self, context: AOCAuthorizationContext) -> bool:
        """Check if agent's role has authority for this action."""
        authorized, reason = check_action_authorization(
            context.agent_profile,
            context.action,
            context.current_phase.value if context.current_phase else None,
        )

        if not authorized:
            logger.debug(f"Role authority check failed: {reason}")
            return False

        return True

    def _check_phase_appropriateness(self, context: AOCAuthorizationContext) -> bool:
        """Check if agent is active in current phase."""
        if not context.current_phase:
            # No phase restriction
            return True

        phase_str = context.current_phase.value
        if phase_str not in context.agent_profile.active_phases:
            logger.debug(
                f"Phase appropriateness check failed: "
                f"agent {context.agent_profile.agent_id} not active in {phase_str}"
            )
            return False

        return True

    def _check_information_access(self, context: AOCAuthorizationContext) -> bool:
        """Check if agent has access to required information category."""
        if not context.information_category:
            return True

        authorized, reason = check_access(
            context.agent_profile,
            context.information_category,
            context.current_phase.value if context.current_phase else None,
        )

        if not authorized:
            logger.debug(f"Information access check failed: {reason}")
            return False

        return True

    def _check_delegation_chain(self, context: AOCAuthorizationContext) -> bool:
        """Check if delegation chain is valid."""
        if not context.delegation_chain:
            return True

        # Check if agent has delegation authority
        if not context.agent_profile.delegation_authority:
            logger.debug(
                f"Delegation chain check failed: "
                f"agent {context.agent_profile.agent_id} lacks delegation authority"
            )
            return False

        # Check delegation depth (max 2 levels)
        if len(context.delegation_chain) > 2:
            logger.debug("Delegation chain check failed: chain too long (max 2)")
            return False

        # Additional validation could check if delegating agent has sufficient access level
        # For now, just validate that chain exists and isn't too long

        return True

    def _check_doctrinal_compliance(self, context: AOCAuthorizationContext) -> bool:
        """
        Check if action complies with doctrine.

        Note: This is a simplified check. In production, this would query
        the doctrine knowledge base to validate the action.
        """
        # Placeholder - would integrate with doctrine KB
        # For now, allow all actions (doctrine compliance checked at execution)
        return True

    def _check_opa_policy(self, context: AOCAuthorizationContext) -> bool:
        """Check if OPA policy allows this action."""
        try:
            # Prepare OPA input
            opa_input = {
                "agent": {
                    "id": context.agent_profile.agent_id,
                    "role": context.agent_profile.role,
                    "access_level": context.agent_profile.access_level.value,
                },
                "action": {
                    "type": context.action,
                    **context.additional_context,
                },
                "ato_cycle": {
                    "current_phase": context.current_phase.value if context.current_phase else None,
                },
            }

            # Query OPA
            response = requests.post(
                f"{self.opa_url}/v1/data/aether/agent_authorization/allow",
                json={"input": opa_input},
                timeout=5,
            )

            if response.status_code != 200:
                logger.warning(f"OPA query failed with status {response.status_code}")
                # Fail open in development, fail closed in production
                return os.getenv("AETHER_ENV", "development") == "development"

            result = response.json()
            allowed = result.get("result", False)

            if not allowed:
                logger.debug(f"OPA policy check failed for action: {context.action}")

            return allowed

        except requests.exceptions.RequestException as e:
            logger.warning(f"OPA server unavailable: {e}")
            # Fail open in development, fail closed in production
            return os.getenv("AETHER_ENV", "development") == "development"
        except Exception as e:
            logger.error(f"Error in OPA policy check: {e}", exc_info=True)
            return False

    def authorize_frequency_allocation(
        self,
        agent_profile: AgentAccessProfile,
        frequency_range: tuple[float, float],
        time_window: tuple[str, str],
        geographic_area: Dict[str, Any],
        current_phase: ATOPhase,
    ) -> AuthorizationDecision:
        """
        Authorize a frequency allocation request.

        This is a convenience method that wraps the general authorization
        with specific context for frequency allocation.
        """
        context = AOCAuthorizationContext(
            agent_profile=agent_profile,
            action="allocate_frequency",
            current_phase=current_phase,
            information_category=InformationCategory.SPECTRUM_ALLOCATION,
            additional_context={
                "frequency_range": frequency_range,
                "time_window": time_window,
                "geographic_area": geographic_area,
            },
        )

        return self.can_agent_act(context)

    def authorize_asset_assignment(
        self,
        agent_profile: AgentAccessProfile,
        asset_id: str,
        mission_id: str,
        time_window: tuple[str, str],
        current_phase: ATOPhase,
    ) -> AuthorizationDecision:
        """
        Authorize an asset assignment request.

        Convenience method for asset assignment authorization.
        """
        context = AOCAuthorizationContext(
            agent_profile=agent_profile,
            action="assign_ems_asset",
            current_phase=current_phase,
            information_category=InformationCategory.ASSET_STATUS,
            additional_context={
                "asset_id": asset_id,
                "mission_id": mission_id,
                "time_window": time_window,
            },
        )

        return self.can_agent_act(context)
