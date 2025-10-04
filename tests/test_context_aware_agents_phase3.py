"""
Tests for Phase 3: Context-Aware Agent Migration.

Tests the migrated context-aware agents:
- ContextAwareEMSStrategyAgent
- ContextAwareEWPlannerAgent
- ContextAwareSpectrumManagerAgent
"""

import pytest
from unittest.mock import Mock
from typing import Dict, Any

from agents.context_aware_ems_strategy_agent import (
    ContextAwareEMSStrategyAgent,
    EMSStrategyResponse,
)
from agents.context_aware_ew_planner_agent import (
    ContextAwareEWPlannerAgent,
    EWMissionPlanResponse,
)
from agents.context_aware_spectrum_manager_agent import (
    ContextAwareSpectrumManagerAgent,
    SpectrumAllocationResponse,
)
from aether_os.agent_context import (
    AgentContext,
    DoctrineContext,
    SituationalContext,
    HistoricalContext,
)
from aether_os.orchestrator import ATOPhase


class TestContextAwareEMSStrategyAgent:
    """Test ContextAwareEMSStrategyAgent."""

    @pytest.fixture
    def mock_aether_os(self):
        """Create mock Aether OS."""
        mock = Mock()
        mock.context_manager = Mock()
        mock.performance_evaluator = Mock()
        return mock

    def test_initialization(self, mock_aether_os):
        """Test agent initialization."""
        agent = ContextAwareEMSStrategyAgent(mock_aether_os)

        assert agent.agent_id == "ems_strategy_agent"
        assert agent.role == "ems_strategy"
        assert agent.semantic_tracker is not None
        assert agent.llm_client is not None

    def test_develop_strategy(self, mock_aether_os):
        """Test strategy development."""
        agent = ContextAwareEMSStrategyAgent(mock_aether_os)

        # Set context
        agent.current_context = AgentContext(
            agent_id="ems_strategy_agent",
            current_phase=ATOPhase.PHASE1_OEG,
            doctrinal_context=DoctrineContext(
                relevant_procedures=[
                    {"content": "Develop EMS strategy aligned with objectives"},
                ],
            ),
            situational_context=SituationalContext(
                current_threats=[
                    {"threat_id": "THR-001", "threat_type": "SAM"},
                ],
            ),
        )

        # Develop strategy (will use fallback without API key)
        response = agent.develop_strategy(
            commanders_guidance="Test guidance",
            mission_objectives=["Objective 1"],
            timeline="72 hours",
        )

        assert response["success"] is True
        assert "content" in response

    def test_validate_strategy_doctrine_compliance(self, mock_aether_os):
        """Test strategy validation."""
        agent = ContextAwareEMSStrategyAgent(mock_aether_os)

        # Set minimal context
        agent.current_context = AgentContext(
            agent_id="ems_strategy_agent",
            current_phase=ATOPhase.PHASE1_OEG,
        )

        response = agent.validate_strategy_doctrine_compliance(
            strategy="Test strategy following doctrine",
        )

        # Should return validation result
        assert response["success"] is True

    def test_identify_strategy_gaps(self, mock_aether_os):
        """Test information gap identification."""
        agent = ContextAwareEMSStrategyAgent(mock_aether_os)

        # No context - should identify gaps
        gaps = agent.identify_strategy_gaps()

        assert isinstance(gaps, list)
        # Should identify missing information
        assert len(gaps) > 0

    def test_handle_message_develop_strategy(self, mock_aether_os):
        """Test message handling for strategy development."""
        agent = ContextAwareEMSStrategyAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="ems_strategy_agent",
            current_phase=ATOPhase.PHASE1_OEG,
        )

        response = agent.handle_message(
            sender="test_sender",
            message_type="develop_strategy",
            payload={
                "guidance": "Test guidance",
                "objectives": ["Objective 1"],
            },
        )

        assert response["success"] is True


class TestContextAwareEWPlannerAgent:
    """Test ContextAwareEWPlannerAgent."""

    @pytest.fixture
    def mock_aether_os(self):
        """Create mock Aether OS."""
        mock = Mock()
        mock.context_manager = Mock()
        mock.performance_evaluator = Mock()
        return mock

    def test_initialization(self, mock_aether_os):
        """Test agent initialization."""
        agent = ContextAwareEWPlannerAgent(mock_aether_os)

        assert agent.agent_id == "ew_planner_agent"
        assert agent.role == "ew_planner"
        assert agent.semantic_tracker is not None

    def test_plan_missions(self, mock_aether_os):
        """Test mission planning."""
        agent = ContextAwareEWPlannerAgent(mock_aether_os)

        # Set context with threats and assets
        agent.current_context = AgentContext(
            agent_id="ew_planner_agent",
            current_phase=ATOPhase.PHASE3_WEAPONEERING,
            situational_context=SituationalContext(
                current_threats=[
                    {
                        "threat_id": "THR-001",
                        "threat_type": "SA-10",
                        "location": {"lat": 36.0, "lon": 44.0},
                    },
                ],
                available_assets=[
                    {
                        "asset_id": "AST-001",
                        "platform": "EA-18G",
                        "capability": "Jamming",
                    },
                ],
            ),
        )

        response = agent.plan_missions(
            mission_type="SEAD",
            targets=["THR-001"],
            timeframe="H-hour to H+4",
        )

        assert response["success"] is True

    def test_check_fratricide(self, mock_aether_os):
        """Test fratricide checking."""
        agent = ContextAwareEWPlannerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="ew_planner_agent",
            current_phase=ATOPhase.PHASE3_WEAPONEERING,
        )

        missions = [
            {
                "mission_id": "M-001",
                "asset_id": "EA-001",
                "target_id": "THR-001",
            },
        ]

        response = agent.check_fratricide(missions)

        assert response["success"] is True

    def test_assign_assets_to_targets(self, mock_aether_os):
        """Test asset assignment."""
        agent = ContextAwareEWPlannerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="ew_planner_agent",
            current_phase=ATOPhase.PHASE3_WEAPONEERING,
        )

        targets = [
            {"threat_id": "THR-001", "threat_type": "SA-10", "priority": "critical"},
        ]

        assets = [
            {"asset_id": "AST-001", "platform": "EA-18G", "capability": "Jamming"},
        ]

        response = agent.assign_assets_to_targets(targets, assets)

        assert response["success"] is True

    def test_handle_message_plan_missions(self, mock_aether_os):
        """Test message handling for mission planning."""
        agent = ContextAwareEWPlannerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="ew_planner_agent",
            current_phase=ATOPhase.PHASE3_WEAPONEERING,
        )

        response = agent.handle_message(
            sender="test_sender",
            message_type="plan_missions",
            payload={
                "mission_type": "SEAD",
                "targets": ["THR-001"],
                "timeframe": "H-hour to H+4",
            },
        )

        assert response["success"] is True


class TestContextAwareSpectrumManagerAgent:
    """Test ContextAwareSpectrumManagerAgent."""

    @pytest.fixture
    def mock_aether_os(self):
        """Create mock Aether OS."""
        mock = Mock()
        mock.context_manager = Mock()
        mock.performance_evaluator = Mock()
        return mock

    def test_initialization(self, mock_aether_os):
        """Test agent initialization."""
        agent = ContextAwareSpectrumManagerAgent(mock_aether_os)

        assert agent.agent_id == "spectrum_manager_agent"
        assert agent.role == "spectrum_manager"
        assert agent.semantic_tracker is not None

    def test_allocate_frequencies(self, mock_aether_os):
        """Test frequency allocation."""
        agent = ContextAwareSpectrumManagerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="spectrum_manager_agent",
            current_phase=ATOPhase.PHASE3_WEAPONEERING,
            doctrinal_context=DoctrineContext(
                relevant_procedures=[
                    {"content": "Follow JCEOI process for allocations"},
                ],
            ),
        )

        requests = [
            {"mission_id": "M-001", "band": "S-band", "priority": "high"},
        ]

        response = agent.allocate_frequencies(requests)

        assert response["success"] is True

    def test_check_conflicts(self, mock_aether_os):
        """Test conflict checking."""
        agent = ContextAwareSpectrumManagerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="spectrum_manager_agent",
            current_phase=ATOPhase.PHASE3_WEAPONEERING,
        )

        allocation = {
            "mission_id": "M-001",
            "frequency_min_mhz": 2000,
            "frequency_max_mhz": 3000,
            "start_time": "H-1",
            "end_time": "H+2",
        }

        response = agent.check_conflicts(allocation)

        assert response["success"] is True

    def test_coordinate_deconfliction(self, mock_aether_os):
        """Test deconfliction coordination."""
        agent = ContextAwareSpectrumManagerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="spectrum_manager_agent",
            current_phase=ATOPhase.PHASE3_WEAPONEERING,
        )

        conflicts = [
            {"description": "Overlapping frequency range"},
        ]

        response = agent.coordinate_deconfliction(conflicts)

        assert response["success"] is True

    def test_emergency_reallocation(self, mock_aether_os):
        """Test emergency reallocation."""
        agent = ContextAwareSpectrumManagerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="spectrum_manager_agent",
            current_phase=ATOPhase.PHASE5_EXECUTION,
        )

        response = agent.emergency_reallocation(
            reason="Jamming interference",
            affected_missions=["M-001"],
            urgency="critical",
        )

        assert response["success"] is True

    def test_handle_message_allocate_frequencies(self, mock_aether_os):
        """Test message handling for frequency allocation."""
        agent = ContextAwareSpectrumManagerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="spectrum_manager_agent",
            current_phase=ATOPhase.PHASE3_WEAPONEERING,
        )

        response = agent.handle_message(
            sender="ew_planner_agent",
            message_type="allocate_frequencies",
            payload={
                "requests": [
                    {"mission_id": "M-001", "band": "S-band"},
                ],
            },
        )

        assert response["success"] is True


def test_agent_integration():
    """Test agents working together."""
    mock_aether_os = Mock()
    mock_aether_os.context_manager = Mock()
    mock_aether_os.performance_evaluator = Mock()

    # Create all agents
    strategy_agent = ContextAwareEMSStrategyAgent(mock_aether_os)
    ew_agent = ContextAwareEWPlannerAgent(mock_aether_os)
    spectrum_agent = ContextAwareSpectrumManagerAgent(mock_aether_os)

    # Set up context
    context = AgentContext(
        agent_id="ems_strategy_agent",
        current_phase=ATOPhase.PHASE1_OEG,
        doctrinal_context=DoctrineContext(
            relevant_procedures=[
                {"content": "Develop comprehensive EMS strategy"},
            ],
        ),
        situational_context=SituationalContext(
            current_threats=[
                {"threat_id": "THR-001", "threat_type": "SAM"},
            ],
            available_assets=[
                {"asset_id": "AST-001", "platform": "EA-18G"},
            ],
        ),
    )

    # Step 1: Strategy development
    strategy_agent.current_context = context
    strategy_response = strategy_agent.develop_strategy(
        commanders_guidance="Test",
        mission_objectives=["Objective 1"],
    )
    assert strategy_response["success"] is True

    # Step 2: Mission planning
    context.agent_id = "ew_planner_agent"
    context.current_phase = ATOPhase.PHASE3_WEAPONEERING
    ew_agent.current_context = context

    mission_response = ew_agent.plan_missions(
        mission_type="SEAD",
        targets=["THR-001"],
        timeframe="H-hour to H+4",
    )
    assert mission_response["success"] is True

    # Step 3: Frequency allocation
    context.agent_id = "spectrum_manager_agent"
    spectrum_agent.current_context = context

    allocation_response = spectrum_agent.allocate_frequencies(
        requests=[{"mission_id": "M-001", "band": "S-band"}],
    )
    assert allocation_response["success"] is True

    print("\n✅ Integration test passed: All 3 agents executed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
