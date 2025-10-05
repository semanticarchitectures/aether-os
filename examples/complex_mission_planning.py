#!/usr/bin/env python3
"""
Complex Mission Planning Example for Aether OS

This example demonstrates how to provide detailed instructions to agents
for complex mission planning scenarios, including:

1. Detailed scenario configuration
2. Multi-layered context provision
3. Structured mission parameters
4. Inter-agent coordination
5. Performance evaluation

Usage:
    python examples/complex_mission_planning.py
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from aether_os.core import AetherOS
from aether_os.orchestrator import ATOPhase
from aether_os.agent_context import AgentContext, DoctrineContext, SituationalContext, HistoricalContext
from agents.context_aware_ew_planner_agent import ContextAwareEWPlannerAgent
from agents.context_aware_spectrum_manager_agent import ContextAwareSpectrumManagerAgent
from agents.context_aware_ems_strategy_agent import ContextAwareEMSStrategyAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ComplexMissionScenario:
    """Complex mission scenario with detailed configuration."""
    
    def __init__(self):
        """Initialize complex mission scenario."""
        self.scenario_id = "COMPLEX_A2AD_001"
        self.name = "Multi-Domain A2/AD Penetration"
        self.description = "Complex mission requiring coordinated EMS operations against layered A2/AD"
        
        # Mission timeline
        self.mission_start = datetime.now() + timedelta(hours=24)
        self.mission_duration = timedelta(hours=8)
        
        # Define complex threat environment
        self.threat_environment = self._build_threat_environment()
        
        # Define available assets
        self.available_assets = self._build_asset_inventory()
        
        # Define mission objectives
        self.mission_objectives = self._build_mission_objectives()
        
        # Define constraints and requirements
        self.constraints = self._build_constraints()
        
        # Define coordination requirements
        self.coordination_requirements = self._build_coordination_requirements()
    
    def _build_threat_environment(self) -> List[Dict[str, Any]]:
        """Build complex layered threat environment."""
        return [
            {
                "threat_id": "IADS-001",
                "threat_type": "Integrated Air Defense System",
                "location": {"lat": 36.0, "lon": 44.0, "elevation": 150},
                "priority": "critical",
                "capability": "Multi-layered air defense",
                "components": [
                    {
                        "component_id": "SAM-001",
                        "type": "S-400 Triumf",
                        "location": {"lat": 36.0, "lon": 44.0},
                        "engagement_range_nm": 250,
                        "frequency_bands": ["C-band", "S-band", "X-band"],
                        "threat_level": "critical",
                        "mobility": "semi-mobile",
                        "operational_status": "active"
                    },
                    {
                        "component_id": "SAM-002", 
                        "type": "S-300PMU2",
                        "location": {"lat": 36.2, "lon": 44.1},
                        "engagement_range_nm": 120,
                        "frequency_bands": ["S-band", "C-band"],
                        "threat_level": "high",
                        "mobility": "mobile",
                        "operational_status": "active"
                    },
                    {
                        "component_id": "SAM-003",
                        "type": "Pantsir-S1",
                        "location": {"lat": 36.1, "lon": 44.05},
                        "engagement_range_nm": 12,
                        "frequency_bands": ["Ka-band", "Ku-band"],
                        "threat_level": "medium",
                        "mobility": "mobile",
                        "operational_status": "active"
                    }
                ],
                "command_control": {
                    "c2_node_id": "C2-001",
                    "location": {"lat": 36.05, "lon": 44.02},
                    "communication_links": ["VHF", "UHF", "SHF"],
                    "backup_systems": True
                }
            },
            {
                "threat_id": "EW-001",
                "threat_type": "Electronic Warfare Complex",
                "location": {"lat": 35.8, "lon": 43.9},
                "priority": "high",
                "capability": "Communications jamming and SIGINT",
                "frequency_coverage": "HF through Ka-band",
                "jamming_power": "high",
                "collection_capability": "signals intelligence"
            },
            {
                "threat_id": "COMMS-001",
                "threat_type": "Military Communications Network",
                "priority": "medium",
                "nodes": [
                    {"node_id": "COMM-001", "location": {"lat": 36.3, "lon": 44.2}, "type": "primary"},
                    {"node_id": "COMM-002", "location": {"lat": 35.9, "lon": 43.8}, "type": "backup"},
                    {"node_id": "COMM-003", "location": {"lat": 36.1, "lon": 44.3}, "type": "relay"}
                ],
                "frequency_bands": ["VHF", "UHF", "SHF"],
                "encryption": "military-grade",
                "redundancy": "high"
            }
        ]
    
    def _build_asset_inventory(self) -> List[Dict[str, Any]]:
        """Build detailed asset inventory."""
        return [
            {
                "asset_id": "EA-001",
                "platform": "EA-18G Growler",
                "squadron": "VAQ-129",
                "capability": "Stand-in jamming",
                "availability": "available",
                "location": {"lat": 34.0, "lon": 42.0},
                "effective_range_nm": 50,
                "frequency_coverage": "C-band through Ka-band",
                "jamming_power": "high",
                "survivability": "high",
                "coordination_systems": ["Link-16", "MIDS"],
                "mission_duration_hours": 4.5,
                "weapons": ["AGM-88 HARM"],
                "special_capabilities": ["AESA radar jamming", "Communications disruption"]
            },
            {
                "asset_id": "EA-002",
                "platform": "EC-130H Compass Call",
                "squadron": "193rd SOW",
                "capability": "Communications jamming",
                "availability": "available",
                "location": {"lat": 33.5, "lon": 41.8},
                "effective_range_nm": 200,
                "frequency_coverage": "VHF through SHF",
                "jamming_power": "very high",
                "survivability": "medium",
                "coordination_systems": ["Link-16", "SATCOM"],
                "mission_duration_hours": 8.0,
                "special_capabilities": ["Direction finding", "Communications intelligence"]
            },
            {
                "asset_id": "EA-003",
                "platform": "F-16CJ Wild Weasel",
                "squadron": "52nd FW",
                "capability": "SEAD",
                "availability": "available",
                "location": {"lat": 34.2, "lon": 42.1},
                "effective_range_nm": 300,
                "survivability": "high",
                "coordination_systems": ["Link-16"],
                "mission_duration_hours": 3.0,
                "weapons": ["AGM-88 HARM", "AGM-154 JSOW"],
                "special_capabilities": ["Radar threat detection", "Precision strike"]
            },
            {
                "asset_id": "ISR-001",
                "platform": "RC-135V/W Rivet Joint",
                "squadron": "55th Wing",
                "capability": "SIGINT collection",
                "availability": "available",
                "location": {"lat": 33.0, "lon": 41.5},
                "effective_range_nm": 500,
                "coordination_systems": ["Link-16", "SATCOM", "JWICS"],
                "mission_duration_hours": 12.0,
                "special_capabilities": ["Real-time SIGINT", "Communications analysis", "Threat geolocation"]
            }
        ]
    
    def _build_mission_objectives(self) -> Dict[str, Any]:
        """Build detailed mission objectives."""
        return {
            "primary_objectives": [
                {
                    "objective_id": "OBJ-001",
                    "description": "Suppress S-400 system to enable strike package penetration",
                    "priority": "critical",
                    "success_criteria": "S-400 radar offline for minimum 30 minutes",
                    "timeline": "H-hour to H+0:30",
                    "coordination": "Must coordinate with Package Alpha TOT"
                },
                {
                    "objective_id": "OBJ-002", 
                    "description": "Disrupt enemy communications during strike window",
                    "priority": "high",
                    "success_criteria": "Communications degraded by 70% during H+0:15 to H+2:00",
                    "timeline": "H+0:15 to H+2:00",
                    "coordination": "Support all strike packages"
                }
            ],
            "secondary_objectives": [
                {
                    "objective_id": "OBJ-003",
                    "description": "Collect SIGINT on backup communication systems",
                    "priority": "medium",
                    "success_criteria": "Identify and characterize backup C2 frequencies",
                    "timeline": "H-2:00 to H+4:00",
                    "coordination": "Deconflict with jamming operations"
                }
            ],
            "force_protection": [
                {
                    "objective_id": "FP-001",
                    "description": "Protect friendly communications from enemy jamming",
                    "priority": "high",
                    "success_criteria": "Maintain 90% friendly communications availability",
                    "timeline": "H-1:00 to H+4:00"
                }
            ]
        }
    
    def _build_constraints(self) -> Dict[str, Any]:
        """Build mission constraints and limitations."""
        return {
            "temporal_constraints": {
                "mission_window": "H-hour to H+4:00",
                "weather_window": "Clear conditions required H-0:30 to H+1:00",
                "coordination_deadlines": {
                    "frequency_requests": "H-24:00",
                    "airspace_coordination": "H-12:00",
                    "final_mission_brief": "H-2:00"
                }
            },
            "geographic_constraints": {
                "no_fly_zones": [
                    {"area": "Civilian airport", "coordinates": [[35.9, 43.7], [35.95, 43.75]]},
                    {"area": "Hospital complex", "coordinates": [[36.05, 44.1], [36.07, 44.12]]}
                ],
                "restricted_areas": [
                    {"area": "Population center", "coordinates": [[36.0, 44.0], [36.1, 44.1]], "altitude_limit": 15000}
                ]
            },
            "spectrum_constraints": {
                "protected_frequencies": [
                    {"band": "121.5 MHz", "purpose": "Emergency"},
                    {"band": "243.0 MHz", "purpose": "Military emergency"},
                    {"band": "406 MHz", "purpose": "Satellite emergency"}
                ],
                "coordination_required": [
                    {"band": "VHF Air Traffic Control", "authority": "Host nation"},
                    {"band": "Military SATCOM", "authority": "DISA"}
                ]
            },
            "rules_of_engagement": {
                "jamming_restrictions": "No jamming of civilian communications",
                "kinetic_restrictions": "Weapons release only on confirmed military targets",
                "collateral_damage": "Minimize civilian impact"
            }
        }
    
    def _build_coordination_requirements(self) -> Dict[str, Any]:
        """Build inter-service and coalition coordination requirements."""
        return {
            "strike_packages": [
                {
                    "package_id": "PKG-ALPHA",
                    "mission": "Primary target strike",
                    "aircraft": ["F-35A x4", "F-16C x2"],
                    "toa": "H+0:30",
                    "target": "Command bunker",
                    "ems_support_required": "SEAD escort, communications jamming"
                },
                {
                    "package_id": "PKG-BRAVO",
                    "mission": "Secondary target strike", 
                    "aircraft": ["F-15E x2", "F-16C x4"],
                    "toa": "H+1:15",
                    "target": "Supply depot",
                    "ems_support_required": "Area jamming, threat warning"
                }
            ],
            "coalition_forces": [
                {
                    "nation": "Partner Nation A",
                    "assets": ["EF-2000 x2"],
                    "role": "Air superiority",
                    "coordination_freq": "251.0 MHz",
                    "liaison": "AWACS Callsign Magic"
                }
            ],
            "supporting_elements": [
                {
                    "element": "AWACS",
                    "callsign": "Magic 01",
                    "frequency": "251.0 MHz",
                    "role": "Air battle management"
                },
                {
                    "element": "Tanker",
                    "callsign": "Shell 01", 
                    "frequency": "265.0 MHz",
                    "role": "Air refueling"
                }
            ]
        }


async def demonstrate_complex_mission_planning():
    """Demonstrate complex mission planning with detailed agent instructions."""
    
    logger.info("=== COMPLEX MISSION PLANNING DEMONSTRATION ===")
    
    # Initialize scenario
    scenario = ComplexMissionScenario()
    logger.info(f"Scenario: {scenario.name}")
    logger.info(f"Mission ID: {scenario.scenario_id}")
    
    # Initialize Aether OS
    aether_os = AetherOS(
        doctrine_kb_path="doctrine_kb/chroma_db",
        opa_url=os.getenv("OPA_URL", "http://localhost:8181")
    )
    
    # Create context-aware agents
    ems_strategy = ContextAwareEMSStrategyAgent(aether_os)
    ew_planner = ContextAwareEWPlannerAgent(aether_os)
    spectrum_manager = ContextAwareSpectrumManagerAgent(aether_os)
    
    # Register agents
    aether_os.register_agent("ems_strategy_agent", ems_strategy)
    aether_os.register_agent("ew_planner_agent", ew_planner)
    aether_os.register_agent("spectrum_manager_agent", spectrum_manager)
    
    logger.info("Agents registered and initialized")
    
    # === PHASE 1: STRATEGIC PLANNING ===
    logger.info("\n" + "="*60)
    logger.info("PHASE 1: EMS STRATEGIC PLANNING")
    logger.info("="*60)
    
    # Provide detailed commander's guidance
    commanders_guidance = """
    COMMANDER'S INTENT: Penetrate layered A2/AD system to enable precision strikes
    on high-value targets while minimizing friendly losses and civilian casualties.
    
    KEY TASKS:
    1. Suppress long-range SAM systems (S-400, S-300) during strike window
    2. Disrupt enemy command and control communications
    3. Protect friendly communications and coordination systems
    4. Collect intelligence on enemy backup systems and procedures
    
    CONSTRAINTS:
    - Minimize civilian impact and collateral damage
    - Coordinate with coalition partners
    - Maintain operational security
    - Preserve assets for follow-on operations
    
    SUCCESS CRITERIA:
    - Strike packages reach targets with minimal attrition
    - Enemy air defense effectiveness reduced by 80%
    - Friendly communications maintained at 90% effectiveness
    """
    
    # Develop EMS strategy with detailed context
    strategy_response = ems_strategy.develop_strategy(
        commanders_guidance=commanders_guidance,
        mission_objectives=[obj["description"] for obj in scenario.mission_objectives["primary_objectives"]],
        timeline="8 hours"
    )
    
    logger.info(f"Strategy development: {'SUCCESS' if strategy_response['success'] else 'FAILED'}")
    if strategy_response['success']:
        logger.info(f"Context utilization: {strategy_response.get('context_utilization', 0):.1%}")
    
    # === PHASE 3: DETAILED MISSION PLANNING ===
    logger.info("\n" + "="*60)
    logger.info("PHASE 3: DETAILED EW MISSION PLANNING")
    logger.info("="*60)
    
    # Provide comprehensive mission planning instructions
    detailed_mission_instructions = {
        "mission_type": "Multi-domain SEAD/EA",
        "threat_environment": scenario.threat_environment,
        "available_assets": scenario.available_assets,
        "mission_objectives": scenario.mission_objectives,
        "constraints": scenario.constraints,
        "coordination_requirements": scenario.coordination_requirements,
        "timeline": {
            "h_hour": scenario.mission_start.isoformat(),
            "mission_duration": str(scenario.mission_duration),
            "key_events": [
                {"time": "H-2:00", "event": "Final coordination complete"},
                {"time": "H-0:30", "event": "EW assets on station"},
                {"time": "H+0:00", "event": "SEAD initiation"},
                {"time": "H+0:30", "event": "Strike Package Alpha TOT"},
                {"time": "H+1:15", "event": "Strike Package Bravo TOT"},
                {"time": "H+4:00", "event": "Mission complete"}
            ]
        },
        "special_instructions": [
            "Prioritize S-400 suppression for Package Alpha success",
            "Coordinate jamming timeline to avoid fratricide with SIGINT collection",
            "Maintain continuous communications protection for friendly forces",
            "Be prepared to adapt to enemy countermeasures",
            "Ensure deconfliction with coalition partner frequencies"
        ]
    }
    
    # Plan complex EW missions
    mission_response = await ew_planner.plan_complex_missions(
        mission_instructions=detailed_mission_instructions,
        cycle_id="ATO-COMPLEX-001"
    )
    
    logger.info(f"Mission planning: {'SUCCESS' if mission_response['success'] else 'FAILED'}")
    if mission_response['success']:
        logger.info(f"Context utilization: {mission_response.get('context_utilization', 0):.1%}")
        logger.info(f"Missions planned: {len(mission_response.get('content', {}).get('missions', []))}")
    
    # === SPECTRUM COORDINATION ===
    logger.info("\n" + "="*60)
    logger.info("SPECTRUM MANAGEMENT & COORDINATION")
    logger.info("="*60)
    
    # Provide detailed spectrum requirements
    spectrum_requirements = {
        "mission_id": scenario.scenario_id,
        "frequency_requests": [
            {
                "requester": "EA-001",
                "frequency_range": (8000, 12000),  # X-band for S-400 jamming
                "time_window": ("H-0:30", "H+1:00"),
                "geographic_area": {"center": {"lat": 36.0, "lon": 44.0}, "radius_nm": 50},
                "priority": "critical",
                "purpose": "S-400 radar jamming"
            },
            {
                "requester": "EA-002", 
                "frequency_range": (225, 400),  # UHF for communications jamming
                "time_window": ("H+0:15", "H+2:00"),
                "geographic_area": {"center": {"lat": 36.0, "lon": 44.0}, "radius_nm": 100},
                "priority": "high",
                "purpose": "Enemy communications disruption"
            }
        ],
        "protected_frequencies": scenario.constraints["spectrum_constraints"]["protected_frequencies"],
        "coordination_requirements": scenario.constraints["spectrum_constraints"]["coordination_required"],
        "deconfliction_requirements": [
            "Avoid interference with ISR-001 SIGINT collection",
            "Coordinate with coalition partner frequencies",
            "Maintain friendly communications protection"
        ]
    }
    
    # Process spectrum allocation
    spectrum_response = await spectrum_manager.process_complex_allocation(
        spectrum_requirements=spectrum_requirements,
        cycle_id="ATO-COMPLEX-001"
    )
    
    logger.info(f"Spectrum allocation: {'SUCCESS' if spectrum_response['success'] else 'FAILED'}")
    if spectrum_response['success']:
        logger.info(f"Allocations processed: {len(spectrum_response.get('content', {}).get('allocations', []))}")
    
    # === RESULTS SUMMARY ===
    logger.info("\n" + "="*60)
    logger.info("COMPLEX MISSION PLANNING RESULTS")
    logger.info("="*60)
    
    logger.info(f"Scenario: {scenario.name}")
    logger.info(f"Threats analyzed: {len(scenario.threat_environment)}")
    logger.info(f"Assets coordinated: {len(scenario.available_assets)}")
    logger.info(f"Objectives addressed: {len(scenario.mission_objectives['primary_objectives'])}")
    
    if strategy_response['success']:
        logger.info("✅ EMS strategy developed successfully")
    else:
        logger.info("❌ EMS strategy development failed")
    
    if mission_response['success']:
        logger.info("✅ Complex mission planning completed")
    else:
        logger.info("❌ Mission planning failed")
    
    if spectrum_response['success']:
        logger.info("✅ Spectrum coordination successful")
    else:
        logger.info("❌ Spectrum coordination failed")
    
    # Show context utilization
    logger.info("\nContext Utilization:")
    for agent_name, response in [
        ("EMS Strategy", strategy_response),
        ("EW Planner", mission_response), 
        ("Spectrum Manager", spectrum_response)
    ]:
        if response['success']:
            utilization = response.get('context_utilization', 0)
            logger.info(f"  {agent_name}: {utilization:.1%}")
    
    logger.info("\n=== DEMONSTRATION COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(demonstrate_complex_mission_planning())
