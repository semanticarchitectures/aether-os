"""
Asset Tracking MCP Server for Aether OS.

Provides MCP tools for EMS asset availability and capabilities queries.

Tools:
- query_ems_asset_availability: Query available EMS assets
- get_ems_asset_capabilities: Get asset capabilities
- reserve_asset: Reserve asset for mission
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class AssetTrackingServer:
    """
    MCP server for EMS asset tracking operations.

    Manages asset availability, capabilities, and reservations.
    """

    def __init__(self, db_connection: Optional[Any] = None):
        """
        Initialize asset tracking server.

        Args:
            db_connection: MongoDB connection (optional for prototype)
        """
        self.db = db_connection
        # In-memory asset data for prototype
        self.assets = self._load_sample_assets()
        self.reservations: List[Dict[str, Any]] = []
        logger.info("AssetTrackingServer initialized")

    def _load_sample_assets(self) -> List[Dict[str, Any]]:
        """Load sample EMS asset data for prototype."""
        return [
            {
                "asset_id": "ASSET-EA-001",
                "platform": "EC-130H",
                "asset_type": "electronic_attack",
                "capabilities": ["jamming", "deception", "high_power_jamming"],
                "frequency_coverage": {
                    "min_mhz": 30,
                    "max_mhz": 3000,
                },
                "status": "available",
                "location": "CONUS",
                "readiness": "mission_ready",
                "crew_status": "qualified",
                "maintenance_due": "2025-10-15",
            },
            {
                "asset_id": "ASSET-EA-002",
                "platform": "EA-18G",
                "asset_type": "electronic_attack",
                "capabilities": ["jamming", "targeting", "strike_support"],
                "frequency_coverage": {
                    "min_mhz": 2000,
                    "max_mhz": 18000,
                },
                "status": "available",
                "location": "Forward Deployed",
                "readiness": "mission_ready",
                "crew_status": "qualified",
                "maintenance_due": "2025-11-01",
            },
            {
                "asset_id": "ASSET-EP-001",
                "platform": "Various",
                "asset_type": "electronic_protect",
                "capabilities": ["gps_anti_jam", "comm_protection", "iff_protection"],
                "frequency_coverage": {
                    "min_mhz": 1000,
                    "max_mhz": 6000,
                },
                "status": "available",
                "location": "Theater",
                "readiness": "mission_ready",
                "crew_status": "qualified",
                "maintenance_due": "2025-10-20",
            },
            {
                "asset_id": "ASSET-ES-001",
                "platform": "RC-135",
                "asset_type": "electronic_warfare_support",
                "capabilities": ["sigint", "threat_warning", "targeting_support"],
                "frequency_coverage": {
                    "min_mhz": 1,
                    "max_mhz": 40000,
                },
                "status": "available",
                "location": "Theater",
                "readiness": "mission_ready",
                "crew_status": "qualified",
                "maintenance_due": "2025-10-10",
            },
            {
                "asset_id": "ASSET-EA-003",
                "platform": "EC-130H",
                "asset_type": "electronic_attack",
                "capabilities": ["jamming", "deception"],
                "frequency_coverage": {
                    "min_mhz": 30,
                    "max_mhz": 3000,
                },
                "status": "maintenance",
                "location": "CONUS",
                "readiness": "not_ready",
                "crew_status": "qualified",
                "maintenance_due": "2025-10-05",
            },
        ]

    def query_ems_asset_availability(
        self,
        asset_types: Optional[List[str]] = None,
        time_window: Optional[Tuple[str, str]] = None,
        capabilities: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query available EMS assets.

        Args:
            asset_types: Filter by asset types
            time_window: Required availability window
            capabilities: Required capabilities
            location: Filter by location

        Returns:
            List of available assets
        """
        logger.info(
            f"Querying asset availability (types={asset_types}, "
            f"capabilities={capabilities})"
        )

        results = []

        for asset in self.assets:
            # Filter by asset type
            if asset_types and asset["asset_type"] not in asset_types:
                continue

            # Filter by location
            if location and asset.get("location") != location:
                continue

            # Filter by capabilities
            if capabilities:
                asset_capabilities = set(asset.get("capabilities", []))
                required_capabilities = set(capabilities)
                if not required_capabilities.issubset(asset_capabilities):
                    continue

            # Check availability in time window
            if time_window:
                if not self._is_asset_available(asset["asset_id"], time_window):
                    continue

            # Only include mission-ready assets
            if asset.get("status") == "available" and asset.get("readiness") == "mission_ready":
                results.append(asset)

        logger.info(f"Found {len(results)} available assets")
        return results

    def get_ems_asset_capabilities(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get capabilities for a specific asset.

        Args:
            asset_id: Asset identifier

        Returns:
            Asset capabilities or None
        """
        logger.info(f"Getting capabilities for asset: {asset_id}")

        for asset in self.assets:
            if asset["asset_id"] == asset_id:
                return {
                    "asset_id": asset_id,
                    "platform": asset["platform"],
                    "asset_type": asset["asset_type"],
                    "capabilities": asset["capabilities"],
                    "frequency_coverage": asset["frequency_coverage"],
                    "status": asset["status"],
                    "readiness": asset["readiness"],
                }

        logger.warning(f"Asset not found: {asset_id}")
        return None

    def reserve_asset(
        self,
        asset_id: str,
        mission_id: str,
        time_window: Tuple[str, str],
        requester: str,
    ) -> Dict[str, Any]:
        """
        Reserve an asset for a mission.

        Args:
            asset_id: Asset identifier
            mission_id: Mission identifier
            time_window: (start_time, end_time)
            requester: Requesting agent/user

        Returns:
            Reservation result
        """
        logger.info(
            f"Reserving asset {asset_id} for mission {mission_id} "
            f"by {requester}"
        )

        # Check if asset exists and is available
        asset = self._get_asset_by_id(asset_id)
        if not asset:
            return {
                "success": False,
                "error": f"Asset {asset_id} not found",
            }

        if asset["status"] != "available":
            return {
                "success": False,
                "error": f"Asset {asset_id} not available (status: {asset['status']})",
            }

        # Check for conflicts
        if not self._is_asset_available(asset_id, time_window):
            return {
                "success": False,
                "error": f"Asset {asset_id} already reserved for time window",
            }

        # Create reservation
        reservation = {
            "reservation_id": f"RES-{len(self.reservations) + 1:06d}",
            "asset_id": asset_id,
            "mission_id": mission_id,
            "time_window": time_window,
            "requester": requester,
            "status": "reserved",
        }

        self.reservations.append(reservation)

        logger.info(f"Asset reserved: {reservation['reservation_id']}")
        return {
            "success": True,
            "reservation": reservation,
        }

    def _get_asset_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get asset by ID."""
        for asset in self.assets:
            if asset["asset_id"] == asset_id:
                return asset
        return None

    def _is_asset_available(
        self,
        asset_id: str,
        time_window: Tuple[str, str],
    ) -> bool:
        """Check if asset is available in time window."""
        # Check existing reservations
        for reservation in self.reservations:
            if reservation["asset_id"] == asset_id:
                # Simplified time overlap check
                # In production would parse ISO timestamps properly
                if reservation["status"] == "reserved":
                    return False

        return True

    def get_tools_manifest(self) -> Dict[str, Any]:
        """Get MCP tools manifest."""
        return {
            "tools": [
                {
                    "name": "query_ems_asset_availability",
                    "description": "Query available EMS assets",
                    "parameters": {
                        "asset_types": {"type": "array", "required": False},
                        "time_window": {"type": "array", "required": False},
                        "capabilities": {"type": "array", "required": False},
                        "location": {"type": "string", "required": False},
                    },
                },
                {
                    "name": "get_ems_asset_capabilities",
                    "description": "Get capabilities for a specific asset",
                    "parameters": {
                        "asset_id": {"type": "string", "required": True},
                    },
                },
                {
                    "name": "reserve_asset",
                    "description": "Reserve an asset for a mission",
                    "parameters": {
                        "asset_id": {"type": "string", "required": True},
                        "mission_id": {"type": "string", "required": True},
                        "time_window": {"type": "array", "required": True},
                        "requester": {"type": "string", "required": True},
                    },
                },
            ]
        }


def create_asset_tracking_server(db_connection: Optional[Any] = None):
    """Create asset tracking MCP server."""
    server = AssetTrackingServer(db_connection=db_connection)
    logger.info("Asset Tracking MCP server created")
    return server
