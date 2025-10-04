"""
Spectrum Database MCP Server for Aether OS.

Provides MCP tools for spectrum management operations.

Tools:
- check_spectrum_conflicts: Check for frequency conflicts
- create_spectrum_allocation: Allocate frequency band
- query_allocations: Query existing allocations
- find_available_frequencies: Find available frequencies
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SpectrumServer:
    """
    MCP server for spectrum database operations.

    In production, would connect to MongoDB spectrum_management.allocations
    and implement full MCP server protocol.
    """

    def __init__(self, db_connection: Optional[Any] = None):
        """
        Initialize spectrum server.

        Args:
            db_connection: MongoDB connection (optional for prototype)
        """
        self.db = db_connection
        # In-memory allocations for prototype
        self.allocations: List[Dict[str, Any]] = []
        logger.info("SpectrumServer initialized")

    def check_spectrum_conflicts(
        self,
        frequency_range: Tuple[float, float],
        time_window: Tuple[str, str],
        geographic_area: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Check for spectrum conflicts.

        Args:
            frequency_range: (min_mhz, max_mhz)
            time_window: (start_time, end_time)
            geographic_area: GeoJSON area

        Returns:
            List of conflicting allocations
        """
        logger.info(
            f"Checking spectrum conflicts: "
            f"{frequency_range[0]}-{frequency_range[1]} MHz"
        )

        conflicts = []

        for allocation in self.allocations:
            # Check frequency overlap
            if self._frequencies_overlap(
                frequency_range,
                (allocation["frequency_min_mhz"], allocation["frequency_max_mhz"]),
            ):
                # Check time overlap
                if self._times_overlap(
                    time_window,
                    (allocation["start_time"], allocation["end_time"]),
                ):
                    # Check geographic overlap
                    if self._areas_overlap(geographic_area, allocation.get("geographic_area")):
                        conflicts.append({
                            "allocation_id": allocation["allocation_id"],
                            "frequency_range": (
                                allocation["frequency_min_mhz"],
                                allocation["frequency_max_mhz"],
                            ),
                            "mission_id": allocation.get("mission_id"),
                            "overlap_mhz": self._calculate_frequency_overlap(
                                frequency_range,
                                (allocation["frequency_min_mhz"], allocation["frequency_max_mhz"]),
                            ),
                        })

        logger.info(f"Found {len(conflicts)} spectrum conflicts")
        return conflicts

    def create_spectrum_allocation(
        self,
        frequency_min_mhz: float,
        frequency_max_mhz: float,
        start_time: str,
        end_time: str,
        mission_id: str,
        geographic_area: Dict[str, Any],
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """
        Create a spectrum allocation.

        Args:
            frequency_min_mhz: Minimum frequency in MHz
            frequency_max_mhz: Maximum frequency in MHz
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            mission_id: Mission identifier
            geographic_area: GeoJSON area
            priority: Allocation priority

        Returns:
            Created allocation
        """
        allocation = {
            "allocation_id": f"ALLOC-{len(self.allocations) + 1:06d}",
            "frequency_min_mhz": frequency_min_mhz,
            "frequency_max_mhz": frequency_max_mhz,
            "start_time": start_time,
            "end_time": end_time,
            "mission_id": mission_id,
            "geographic_area": geographic_area,
            "priority": priority,
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }

        self.allocations.append(allocation)

        logger.info(f"Created spectrum allocation: {allocation['allocation_id']}")
        return allocation

    def query_allocations(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query spectrum allocations.

        Args:
            filters: Query filters (e.g., mission_id, status)

        Returns:
            List of matching allocations
        """
        logger.info(f"Querying allocations with filters: {filters}")

        if not filters:
            return self.allocations

        results = []
        for allocation in self.allocations:
            match = True
            for key, value in filters.items():
                if allocation.get(key) != value:
                    match = False
                    break
            if match:
                results.append(allocation)

        logger.info(f"Query returned {len(results)} allocations")
        return results

    def find_available_frequencies(
        self,
        bandwidth_mhz: float,
        time_window: Tuple[str, str],
        geographic_area: Dict[str, Any],
        frequency_band: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find available frequencies.

        Args:
            bandwidth_mhz: Required bandwidth in MHz
            time_window: Time window for allocation
            geographic_area: Geographic area
            frequency_band: Preferred frequency band (optional)

        Returns:
            List of available frequency ranges
        """
        logger.info(f"Finding available frequencies: {bandwidth_mhz} MHz bandwidth")

        # Define frequency bands
        bands = {
            "S-band": (2000.0, 4000.0),
            "C-band": (4000.0, 8000.0),
            "X-band": (8000.0, 12000.0),
        }

        # For prototype, return some available ranges
        available = []

        if frequency_band and frequency_band in bands:
            band_range = bands[frequency_band]
            # Check if band is available
            conflicts = self.check_spectrum_conflicts(
                frequency_range=band_range,
                time_window=time_window,
                geographic_area=geographic_area,
            )

            if not conflicts:
                available.append({
                    "band": frequency_band,
                    "frequency_min_mhz": band_range[0],
                    "frequency_max_mhz": band_range[0] + bandwidth_mhz,
                    "bandwidth_mhz": bandwidth_mhz,
                })

        # If no specific band or band not available, search all bands
        if not available:
            for band_name, band_range in bands.items():
                conflicts = self.check_spectrum_conflicts(
                    frequency_range=band_range,
                    time_window=time_window,
                    geographic_area=geographic_area,
                )

                if not conflicts:
                    available.append({
                        "band": band_name,
                        "frequency_min_mhz": band_range[0],
                        "frequency_max_mhz": band_range[0] + bandwidth_mhz,
                        "bandwidth_mhz": bandwidth_mhz,
                    })

        logger.info(f"Found {len(available)} available frequency ranges")
        return available

    def _frequencies_overlap(
        self,
        range1: Tuple[float, float],
        range2: Tuple[float, float],
    ) -> bool:
        """Check if two frequency ranges overlap."""
        return not (range1[1] <= range2[0] or range2[1] <= range1[0])

    def _times_overlap(
        self,
        time1: Tuple[str, str],
        time2: Tuple[str, str],
    ) -> bool:
        """Check if two time windows overlap."""
        # Simplified - in production would parse ISO timestamps
        return True  # For prototype, assume overlap

    def _areas_overlap(
        self,
        area1: Optional[Dict[str, Any]],
        area2: Optional[Dict[str, Any]],
    ) -> bool:
        """Check if two geographic areas overlap."""
        # Simplified - in production would use geospatial operations
        return True  # For prototype, assume overlap

    def _calculate_frequency_overlap(
        self,
        range1: Tuple[float, float],
        range2: Tuple[float, float],
    ) -> float:
        """Calculate frequency overlap in MHz."""
        overlap_start = max(range1[0], range2[0])
        overlap_end = min(range1[1], range2[1])
        return max(0, overlap_end - overlap_start)

    def get_tools_manifest(self) -> Dict[str, Any]:
        """Get MCP tools manifest."""
        return {
            "tools": [
                {
                    "name": "check_spectrum_conflicts",
                    "description": "Check for frequency conflicts",
                    "parameters": {
                        "frequency_range": {"type": "array", "required": True},
                        "time_window": {"type": "array", "required": True},
                        "geographic_area": {"type": "object", "required": True},
                    },
                },
                {
                    "name": "create_spectrum_allocation",
                    "description": "Create a spectrum allocation",
                    "parameters": {
                        "frequency_min_mhz": {"type": "number", "required": True},
                        "frequency_max_mhz": {"type": "number", "required": True},
                        "start_time": {"type": "string", "required": True},
                        "end_time": {"type": "string", "required": True},
                        "mission_id": {"type": "string", "required": True},
                        "geographic_area": {"type": "object", "required": True},
                        "priority": {"type": "string", "required": False},
                    },
                },
                {
                    "name": "query_allocations",
                    "description": "Query existing spectrum allocations",
                    "parameters": {
                        "filters": {"type": "object", "required": False},
                    },
                },
                {
                    "name": "find_available_frequencies",
                    "description": "Find available frequency ranges",
                    "parameters": {
                        "bandwidth_mhz": {"type": "number", "required": True},
                        "time_window": {"type": "array", "required": True},
                        "geographic_area": {"type": "object", "required": True},
                        "frequency_band": {"type": "string", "required": False},
                    },
                },
            ]
        }


def create_spectrum_server(db_connection: Optional[Any] = None):
    """Create spectrum MCP server."""
    server = SpectrumServer(db_connection=db_connection)
    logger.info("Spectrum MCP server created")
    return server
