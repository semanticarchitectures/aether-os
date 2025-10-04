"""
Threat Intelligence MCP Server for Aether OS.

Provides MCP tools for threat intelligence queries with access control and sanitization.

Tools:
- query_ems_threats: Query EMS threats
- get_threat_frequencies: Get threat frequency data
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ThreatIntelServer:
    """
    MCP server for threat intelligence operations.

    Provides sanitized threat data based on requester's access level.
    """

    def __init__(self, db_connection: Optional[Any] = None):
        """
        Initialize threat intel server.

        Args:
            db_connection: MongoDB connection (optional for prototype)
        """
        self.db = db_connection
        # In-memory threat data for prototype
        self.threats = self._load_sample_threats()
        logger.info("ThreatIntelServer initialized")

    def _load_sample_threats(self) -> List[Dict[str, Any]]:
        """Load sample threat data for prototype."""
        return [
            {
                "threat_id": "THREAT-001",
                "threat_type": "SAM",
                "threat_name": "SA-10",
                "location": {
                    "type": "Point",
                    "coordinates": [44.5, 33.2],
                },
                "frequency_bands": ["S-band", "X-band"],
                "frequency_details": {
                    "search_radar": {"min_mhz": 2800, "max_mhz": 2900},
                    "track_radar": {"min_mhz": 9000, "max_mhz": 9500},
                },
                "classification": "OPERATIONAL",
                "capabilities": ["long_range_sam", "multi_target"],
                "status": "active",
                "last_observed": "2025-10-02T14:00:00Z",
                "sources": ["SIGINT", "IMINT"],  # Sensitive field
                "collection_methods": ["RV-01", "SAT-03"],  # Sensitive field
            },
            {
                "threat_id": "THREAT-002",
                "threat_type": "RADAR",
                "threat_name": "Early Warning Radar",
                "location": {
                    "type": "Point",
                    "coordinates": [45.0, 34.0],
                },
                "frequency_bands": ["VHF"],
                "frequency_details": {
                    "operating_freq": {"min_mhz": 150, "max_mhz": 200},
                },
                "classification": "OPERATIONAL",
                "capabilities": ["early_warning", "wide_area_search"],
                "status": "active",
                "last_observed": "2025-10-02T16:00:00Z",
                "sources": ["SIGINT"],
                "collection_methods": ["RV-01"],
            },
            {
                "threat_id": "THREAT-003",
                "threat_type": "COMMUNICATIONS",
                "threat_name": "Command Network",
                "location": {
                    "type": "Polygon",
                    "coordinates": [[[44.0, 33.0], [46.0, 33.0], [46.0, 35.0], [44.0, 35.0], [44.0, 33.0]]],
                },
                "frequency_bands": ["UHF", "SHF"],
                "frequency_details": {
                    "primary_freq": {"min_mhz": 4000, "max_mhz": 4100},
                    "backup_freq": {"min_mhz": 6000, "max_mhz": 6100},
                },
                "classification": "SENSITIVE",
                "capabilities": ["command_control", "encrypted"],
                "status": "active",
                "last_observed": "2025-10-02T18:00:00Z",
                "sources": ["SIGINT", "HUMINT"],
                "collection_methods": ["RV-01", "ASSET-ALPHA"],
            },
        ]

    def query_ems_threats(
        self,
        geographic_area: Optional[Dict[str, Any]] = None,
        threat_types: Optional[List[str]] = None,
        access_level: int = 3,  # OPERATIONAL by default
    ) -> List[Dict[str, Any]]:
        """
        Query EMS threats with access control.

        Args:
            geographic_area: GeoJSON area (optional)
            threat_types: List of threat types to filter (optional)
            access_level: Requester's access level (1-5)

        Returns:
            List of sanitized threat data
        """
        logger.info(
            f"Querying EMS threats (access_level={access_level}, "
            f"types={threat_types})"
        )

        results = []

        for threat in self.threats:
            # Filter by threat type
            if threat_types and threat["threat_type"] not in threat_types:
                continue

            # Filter by classification vs access level
            threat_classification = threat.get("classification", "OPERATIONAL")
            if not self._check_classification_access(threat_classification, access_level):
                continue

            # Filter by geographic area (simplified)
            # In production would do proper geospatial query

            # Sanitize threat data based on access level
            sanitized_threat = self._sanitize_threat(threat, access_level)
            results.append(sanitized_threat)

        logger.info(f"Query returned {len(results)} threats")
        return results

    def get_threat_frequencies(
        self,
        threat_ids: List[str],
        access_level: int = 3,
    ) -> Dict[str, Any]:
        """
        Get frequency data for specific threats.

        Args:
            threat_ids: List of threat IDs
            access_level: Requester's access level

        Returns:
            Frequency data for threats
        """
        logger.info(f"Getting frequencies for threats: {threat_ids}")

        frequency_data = {}

        for threat_id in threat_ids:
            threat = self._get_threat_by_id(threat_id)
            if threat:
                # Check access
                threat_classification = threat.get("classification", "OPERATIONAL")
                if self._check_classification_access(threat_classification, access_level):
                    frequency_data[threat_id] = {
                        "threat_id": threat_id,
                        "threat_name": threat.get("threat_name"),
                        "frequency_bands": threat.get("frequency_bands"),
                        "frequency_details": threat.get("frequency_details")
                        if access_level >= 4
                        else None,
                    }

        return frequency_data

    def _get_threat_by_id(self, threat_id: str) -> Optional[Dict[str, Any]]:
        """Get threat by ID."""
        for threat in self.threats:
            if threat["threat_id"] == threat_id:
                return threat
        return None

    def _check_classification_access(
        self,
        classification: str,
        access_level: int,
    ) -> bool:
        """Check if access level permits viewing classification."""
        classification_levels = {
            "PUBLIC": 1,
            "INTERNAL": 2,
            "OPERATIONAL": 3,
            "SENSITIVE": 4,
            "CRITICAL": 5,
        }

        required_level = classification_levels.get(classification, 3)
        return access_level >= required_level

    def _sanitize_threat(
        self,
        threat: Dict[str, Any],
        access_level: int,
    ) -> Dict[str, Any]:
        """
        Sanitize threat data based on access level.

        Removes sensitive fields for lower access levels.
        """
        sanitized = threat.copy()

        # Remove highly sensitive fields for access level < SENSITIVE (4)
        if access_level < 4:
            sanitized.pop("sources", None)
            sanitized.pop("collection_methods", None)
            sanitized.pop("frequency_details", None)
            sanitized["frequency_bands_only"] = True

        # Remove critical details for access level < CRITICAL (5)
        if access_level < 5:
            if "frequency_details" in sanitized:
                # Reduce precision
                for key in sanitized.get("frequency_details", {}):
                    if isinstance(sanitized["frequency_details"][key], dict):
                        # Round to nearest 100 MHz
                        freq_range = sanitized["frequency_details"][key]
                        freq_range["min_mhz"] = round(freq_range["min_mhz"] / 100) * 100
                        freq_range["max_mhz"] = round(freq_range["max_mhz"] / 100) * 100

        return sanitized

    def get_tools_manifest(self) -> Dict[str, Any]:
        """Get MCP tools manifest."""
        return {
            "tools": [
                {
                    "name": "query_ems_threats",
                    "description": "Query EMS threats with access control",
                    "parameters": {
                        "geographic_area": {"type": "object", "required": False},
                        "threat_types": {"type": "array", "required": False},
                        "access_level": {"type": "integer", "required": True},
                    },
                },
                {
                    "name": "get_threat_frequencies",
                    "description": "Get frequency data for specific threats",
                    "parameters": {
                        "threat_ids": {"type": "array", "required": True},
                        "access_level": {"type": "integer", "required": True},
                    },
                },
            ]
        }


def create_threat_intel_server(db_connection: Optional[Any] = None):
    """Create threat intel MCP server."""
    server = ThreatIntelServer(db_connection=db_connection)
    logger.info("Threat Intel MCP server created")
    return server
