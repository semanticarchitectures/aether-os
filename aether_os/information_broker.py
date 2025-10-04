"""
Information Broker for Aether OS.

Provides centralized information access with access control, sanitization,
and audit logging. Routes queries to appropriate data sources (doctrine KB,
MCP servers, databases).
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from aether_os.access_control import (
    AgentAccessProfile,
    InformationCategory,
    ACCESS_POLICIES,
    check_access,
)
from aether_os.doctrine_kb import DoctrineKnowledgeBase

logger = logging.getLogger(__name__)


class AOCInformationBroker:
    """
    Centralized information access broker.

    Routes information requests to appropriate sources, enforces access control,
    sanitizes data based on access level, and logs access for audit.
    """

    def __init__(self, doctrine_kb: Optional[DoctrineKnowledgeBase] = None):
        """
        Initialize the information broker.

        Args:
            doctrine_kb: Doctrine knowledge base instance
        """
        self.doctrine_kb = doctrine_kb or DoctrineKnowledgeBase()
        self.audit_log: List[Dict[str, Any]] = []
        self.mcp_clients: Dict[str, Any] = {}  # MCP server clients

        logger.info("AOCInformationBroker initialized")

    def query(
        self,
        agent_profile: AgentAccessProfile,
        category: InformationCategory,
        query_params: Dict[str, Any],
        current_phase: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query information with access control and sanitization.

        Args:
            agent_profile: Agent making the request
            category: Category of information being requested
            query_params: Query parameters
            current_phase: Current ATO phase

        Returns:
            Dictionary with 'success', 'data', and optional 'error' keys
        """
        # Check access
        access_granted, denial_reason = check_access(
            agent_profile, category, current_phase
        )

        if not access_granted:
            logger.warning(
                f"Access denied: agent={agent_profile.agent_id}, "
                f"category={category.name}, reason={denial_reason}"
            )
            return {
                "success": False,
                "error": denial_reason,
                "data": None,
            }

        # Route to appropriate data source
        try:
            if category == InformationCategory.DOCTRINE:
                data = self._query_doctrine(query_params)
            elif category == InformationCategory.THREAT_DATA:
                data = self._query_threats(agent_profile, query_params)
            elif category == InformationCategory.SPECTRUM_ALLOCATION:
                data = self._query_spectrum(query_params)
            elif category == InformationCategory.ASSET_STATUS:
                data = self._query_assets(query_params)
            elif category == InformationCategory.MISSION_PLAN:
                data = self._query_missions(agent_profile, query_params)
            elif category == InformationCategory.ORGANIZATIONAL:
                data = self._query_organizational(query_params)
            elif category == InformationCategory.PROCESS_METRICS:
                data = self._query_process_metrics(query_params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown category: {category}",
                    "data": None,
                }

            # Sanitize if required
            policy = ACCESS_POLICIES[category]
            if policy.sanitization_required:
                data = self._sanitize_data(data, agent_profile, category)

            # Audit if required
            if policy.audit_required:
                self._log_access(agent_profile, category, query_params, current_phase)

            return {
                "success": True,
                "data": data,
            }

        except Exception as e:
            logger.error(
                f"Error querying information: category={category.name}, error={e}",
                exc_info=True,
            )
            return {
                "success": False,
                "error": str(e),
                "data": None,
            }

    def _query_doctrine(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query doctrine knowledge base."""
        query = query_params.get("query", "")
        filters = query_params.get("filters")
        top_k = query_params.get("top_k", 5)

        results = self.doctrine_kb.query(query, filters, top_k)
        logger.debug(f"Doctrine query returned {len(results)} results")
        return results

    def _query_threats(
        self,
        agent_profile: AgentAccessProfile,
        query_params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Query threat intelligence (via MCP server).

        Note: This is a placeholder - would use MCP client to query threat_intel_server
        """
        # Placeholder implementation
        logger.debug(f"Threat query requested by {agent_profile.agent_id}")

        # In production, would call:
        # return self.mcp_clients['threat_intel'].query_ems_threats(query_params)

        return [{
            "threat_id": "THREAT-001",
            "threat_type": "SAM",
            "location": {"type": "Point", "coordinates": [44.5, 33.2]},
            "frequency_bands": ["S-band", "X-band"],
            "classification": "OPERATIONAL",
            "note": "Placeholder data - integrate with threat_intel MCP server",
        }]

    def _query_spectrum(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query spectrum allocations (via MCP server).

        Note: This is a placeholder - would use MCP client to query spectrum_server
        """
        logger.debug("Spectrum query requested")

        # In production, would call:
        # return self.mcp_clients['spectrum'].query_allocations(query_params)

        return [{
            "allocation_id": "ALLOC-001",
            "frequency_min_mhz": 2400.0,
            "frequency_max_mhz": 2500.0,
            "start_time": "2025-10-03T10:00:00Z",
            "end_time": "2025-10-03T14:00:00Z",
            "mission_id": "MISSION-001",
            "note": "Placeholder data - integrate with spectrum MCP server",
        }]

    def _query_assets(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query EMS asset status (via MCP server).

        Note: This is a placeholder - would use MCP client to query asset_tracking_server
        """
        logger.debug("Asset query requested")

        # In production, would call:
        # return self.mcp_clients['asset_tracking'].query_ems_asset_availability(query_params)

        return [{
            "asset_id": "ASSET-EA-001",
            "platform": "EC-130H",
            "asset_type": "electronic_attack",
            "capabilities": ["jamming", "deception"],
            "status": "available",
            "note": "Placeholder data - integrate with asset_tracking MCP server",
        }]

    def _query_missions(
        self,
        agent_profile: AgentAccessProfile,
        query_params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Query mission plans.

        Note: This is a placeholder - would query mission database
        """
        logger.debug(f"Mission query requested by {agent_profile.agent_id}")

        return [{
            "mission_id": "MISSION-001",
            "mission_type": "EW_SUPPORT",
            "ems_objectives": ["Suppress enemy air defenses"],
            "assigned_assets": ["ASSET-EA-001"],
            "note": "Placeholder data - integrate with mission database",
        }]

    def _query_organizational(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query organizational information.

        Note: This is a placeholder - would query org database
        """
        logger.debug("Organizational query requested")

        return {
            "organization": "Combined Air Operations Center",
            "units": ["EMS Division", "Strategy Division", "Combat Plans Division"],
            "note": "Placeholder data - integrate with org database",
        }

    def _query_process_metrics(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query process metrics.

        Note: This is a placeholder - would query metrics database
        """
        logger.debug("Process metrics query requested")

        return {
            "avg_cycle_time_hours": 68.5,
            "phase_completion_rates": {
                "PHASE1_OEG": 0.95,
                "PHASE2_TARGET_DEVELOPMENT": 0.92,
                "PHASE3_WEAPONEERING": 0.88,
            },
            "note": "Placeholder data - integrate with metrics database",
        }

    def _sanitize_data(
        self,
        data: Any,
        agent_profile: AgentAccessProfile,
        category: InformationCategory,
    ) -> Any:
        """
        Sanitize data based on agent's access level.

        Removes or redacts sensitive information that agent shouldn't see.
        """
        if category == InformationCategory.THREAT_DATA:
            return self._sanitize_threat_data(data, agent_profile)
        elif category == InformationCategory.MISSION_PLAN:
            return self._sanitize_mission_data(data, agent_profile)
        else:
            return data

    def _sanitize_threat_data(
        self,
        data: Any,
        agent_profile: AgentAccessProfile,
    ) -> Any:
        """Sanitize threat intelligence based on access level."""
        # If list, sanitize each item
        if isinstance(data, list):
            return [self._sanitize_threat_data(item, agent_profile) for item in data]

        # If not dict, return as-is
        if not isinstance(data, dict):
            return data

        sanitized = data.copy()

        # Remove highly classified fields for lower access levels
        if agent_profile.access_level.value < 4:  # Below SENSITIVE
            sanitized.pop("sources", None)
            sanitized.pop("collection_methods", None)

        return sanitized

    def _sanitize_mission_data(
        self,
        data: Any,
        agent_profile: AgentAccessProfile,
    ) -> Any:
        """Sanitize mission plan data based on access level."""
        # If list, sanitize each item
        if isinstance(data, list):
            return [self._sanitize_mission_data(item, agent_profile) for item in data]

        # If not dict, return as-is
        if not isinstance(data, dict):
            return data

        sanitized = data.copy()

        # Remove sensitive fields for lower access levels
        if agent_profile.access_level.value < 5:  # Below CRITICAL
            sanitized.pop("full_target_coordinates", None)
            sanitized.pop("weapon_specifics", None)

        return sanitized

    def _log_access(
        self,
        agent_profile: AgentAccessProfile,
        category: InformationCategory,
        query_params: Dict[str, Any],
        current_phase: Optional[str],
    ) -> None:
        """Log information access for audit."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_profile.agent_id,
            "agent_role": agent_profile.role,
            "category": category.name,
            "query_params": query_params,
            "phase": current_phase,
        }

        self.audit_log.append(audit_entry)

        logger.info(
            f"Access logged: agent={agent_profile.agent_id}, "
            f"category={category.name}, phase={current_phase}"
        )

    def get_audit_log(
        self,
        agent_id: Optional[str] = None,
        category: Optional[InformationCategory] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit log entries.

        Args:
            agent_id: Filter by agent (optional)
            category: Filter by category (optional)

        Returns:
            List of audit log entries
        """
        filtered_log = self.audit_log

        if agent_id:
            filtered_log = [e for e in filtered_log if e["agent_id"] == agent_id]

        if category:
            filtered_log = [e for e in filtered_log if e["category"] == category.name]

        return filtered_log

    def register_mcp_client(self, name: str, client: Any) -> None:
        """
        Register an MCP server client.

        Args:
            name: Client name (e.g., 'doctrine', 'spectrum', 'threat_intel')
            client: MCP client instance
        """
        self.mcp_clients[name] = client
        logger.info(f"Registered MCP client: {name}")
