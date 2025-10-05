"""
Tests for Phase 4: Context-Aware Agent Migration (ATO Producer & Assessment).

Tests the final two migrated context-aware agents:
- ContextAwareATOProducerAgent
- ContextAwareAssessmentAgent
"""

import pytest
from unittest.mock import Mock
from typing import Dict, Any

from agents.context_aware_ato_producer_agent import (
    ContextAwareATOProducerAgent,
    ATOProducerResponse,
)
from agents.context_aware_assessment_agent import (
    ContextAwareAssessmentAgent,
    AssessmentResponse,
)
from aether_os.agent_context import (
    AgentContext,
    DoctrineContext,
    SituationalContext,
    HistoricalContext,
)
from aether_os.orchestrator import ATOPhase


class TestContextAwareATOProducerAgent:
    """Test ContextAwareATOProducerAgent."""

    @pytest.fixture
    def mock_aether_os(self):
        """Create mock Aether OS."""
        mock = Mock()
        mock.context_manager = Mock()
        mock.performance_evaluator = Mock()
        return mock

    def test_initialization(self, mock_aether_os):
        """Test agent initialization."""
        agent = ContextAwareATOProducerAgent(mock_aether_os)

        assert agent.agent_id == "ato_producer_agent"
        assert agent.role == "ato_producer"
        assert agent.semantic_tracker is not None
        assert agent.llm_client is not None

    def test_produce_ato_ems_annex(self, mock_aether_os):
        """Test ATO EMS annex production."""
        agent = ContextAwareATOProducerAgent(mock_aether_os)

        # Set context
        agent.current_context = AgentContext(
            agent_id="ato_producer_agent",
            current_phase=ATOPhase.PHASE4_ATO_PRODUCTION,
            doctrinal_context=DoctrineContext(
                relevant_procedures=[
                    {"content": "Produce ATO following standard format"},
                    {"content": "Validate all mission approvals"},
                ],
            ),
            situational_context=SituationalContext(
                active_missions=[
                    {"mission_id": "M-001", "mission_type": "EA", "approved": True},
                ],
            ),
        )

        # Sample missions and allocations
        ew_missions = [
            {
                "mission_id": "M-001",
                "mission_type": "EA",
                "target_id": "THR-001",
                "approved": True,
            },
        ]

        frequency_allocations = [
            {
                "mission_id": "M-001",
                "frequency_min_mhz": 2000,
                "frequency_max_mhz": 3000,
                "start_time": "H-1",
                "end_time": "H+2",
            },
        ]

        # Produce ATO annex (will use fallback without API key)
        response = agent.produce_ato_ems_annex(ew_missions, frequency_allocations)

        assert response["success"] is True
        assert "content" in response

    def test_validate_mission_approvals(self, mock_aether_os):
        """Test mission approval validation."""
        agent = ContextAwareATOProducerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="ato_producer_agent",
            current_phase=ATOPhase.PHASE4_ATO_PRODUCTION,
            doctrinal_context=DoctrineContext(
                relevant_procedures=[
                    {"content": "EA missions require O-6 approval"},
                ],
            ),
        )

        missions = [
            {"mission_id": "M-001", "mission_type": "EA", "approved": True},
            {"mission_id": "M-002", "mission_type": "SEAD", "approved": False},
        ]

        response = agent.validate_mission_approvals(missions)

        assert response["success"] is True

    def test_integrate_ems_with_strikes(self, mock_aether_os):
        """Test EMS integration with strike packages."""
        agent = ContextAwareATOProducerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="ato_producer_agent",
            current_phase=ATOPhase.PHASE4_ATO_PRODUCTION,
        )

        ew_missions = [
            {"mission_id": "M-001", "mission_type": "EA", "toa": "H-hour"},
        ]

        strike_packages = [
            {"package_id": "PKG-001", "targets": ["THR-001"], "toa": "H+1"},
        ]

        response = agent.integrate_ems_with_strikes(ew_missions, strike_packages)

        assert response["success"] is True

    def test_generate_spins_annex(self, mock_aether_os):
        """Test SPINS annex generation."""
        agent = ContextAwareATOProducerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="ato_producer_agent",
            current_phase=ATOPhase.PHASE4_ATO_PRODUCTION,
            doctrinal_context=DoctrineContext(
                relevant_procedures=[
                    {"content": "SPINS must include frequency management procedures"},
                    {"content": "Include emergency procedures in SPINS"},
                ],
            ),
        )

        missions = [
            {"mission_id": "M-001", "mission_type": "EA"},
        ]

        allocations = [
            {
                "mission_id": "M-001",
                "frequency_min_mhz": 2000,
                "frequency_max_mhz": 3000,
            },
        ]

        response = agent.generate_spins_annex(missions, allocations)

        assert response["success"] is True

    def test_validate_ato_completeness(self, mock_aether_os):
        """Test ATO completeness validation."""
        agent = ContextAwareATOProducerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="ato_producer_agent",
            current_phase=ATOPhase.PHASE4_ATO_PRODUCTION,
        )

        ato_document = {
            "missions": [{"mission_id": "M-001"}],
            "allocations": [{"mission_id": "M-001"}],
            "spins": {"version": "1.0"},
        }

        response = agent.validate_ato_completeness(ato_document)

        assert response["success"] is True

    def test_handle_message_produce_ato(self, mock_aether_os):
        """Test message handling for ATO production."""
        agent = ContextAwareATOProducerAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="ato_producer_agent",
            current_phase=ATOPhase.PHASE4_ATO_PRODUCTION,
        )

        response = agent.handle_message(
            sender="ew_planner_agent",
            message_type="produce_ato",
            payload={
                "ew_missions": [
                    {"mission_id": "M-001", "mission_type": "EA"},
                ],
                "frequency_allocations": [
                    {"mission_id": "M-001", "frequency_min_mhz": 2000},
                ],
            },
        )

        assert response["success"] is True


class TestContextAwareAssessmentAgent:
    """Test ContextAwareAssessmentAgent."""

    @pytest.fixture
    def mock_aether_os(self):
        """Create mock Aether OS."""
        mock = Mock()
        mock.context_manager = Mock()
        mock.performance_evaluator = Mock()
        mock.improvement_logger = Mock()

        # Mock improvement logger methods
        mock.improvement_logger.get_flags_by_cycle.return_value = []
        mock.improvement_logger.analyze_patterns.return_value = []

        return mock

    def test_initialization(self, mock_aether_os):
        """Test agent initialization."""
        agent = ContextAwareAssessmentAgent(mock_aether_os)

        assert agent.agent_id == "assessment_agent"
        assert agent.role == "assessment"
        assert agent.semantic_tracker is not None
        assert agent.llm_client is not None

    def test_assess_mission_effectiveness(self, mock_aether_os):
        """Test mission effectiveness assessment."""
        agent = ContextAwareAssessmentAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="assessment_agent",
            current_phase=ATOPhase.PHASE6_ASSESSMENT,
            doctrinal_context=DoctrineContext(
                relevant_procedures=[
                    {"content": "Assess mission success rate and effectiveness"},
                ],
            ),
        )

        missions = [
            {"mission_id": "M-001", "status": "success", "mission_type": "EA"},
            {"mission_id": "M-002", "status": "success", "mission_type": "SEAD"},
            {"mission_id": "M-003", "status": "failed", "mission_type": "EA"},
        ]

        execution_data = {
            "total_time": "24 hours",
            "objectives_met": 2,
        }

        response = agent.assess_mission_effectiveness(missions, execution_data)

        assert response["success"] is True

    def test_analyze_process_efficiency(self, mock_aether_os):
        """Test process efficiency analysis."""
        agent = ContextAwareAssessmentAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="assessment_agent",
            current_phase=ATOPhase.PHASE6_ASSESSMENT,
        )

        # Mock will return empty flags
        response = agent.analyze_process_efficiency(cycle_id="CYCLE-001")

        assert response["success"] is True

    def test_generate_lessons_learned(self, mock_aether_os):
        """Test lessons learned generation."""
        agent = ContextAwareAssessmentAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="assessment_agent",
            current_phase=ATOPhase.PHASE6_ASSESSMENT,
            doctrinal_context=DoctrineContext(
                relevant_procedures=[
                    {"content": "Generate lessons learned from assessment"},
                ],
            ),
            historical_context=HistoricalContext(
                lessons_learned=[
                    "Previous lesson: Coordinate EA timing with strikes",
                ],
            ),
        )

        mission_assessment = {
            "success_rate": 0.75,
            "failures": ["M-003 failed due to spectrum conflict"],
        }

        process_assessment = {
            "critical_issues": 2,
            "time_wasted_hours": 5.5,
        }

        response = agent.generate_lessons_learned(
            cycle_id="CYCLE-001",
            mission_assessment=mission_assessment,
            process_assessment=process_assessment,
        )

        assert response["success"] is True

    def test_assess_doctrine_effectiveness(self, mock_aether_os):
        """Test doctrine effectiveness assessment (Option C)."""
        agent = ContextAwareAssessmentAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="assessment_agent",
            current_phase=ATOPhase.PHASE6_ASSESSMENT,
            doctrinal_context=DoctrineContext(
                relevant_procedures=[
                    {"content": "Assess if doctrine procedures worked as expected"},
                ],
            ),
        )

        response = agent.assess_doctrine_effectiveness(cycle_id="CYCLE-001")

        assert response["success"] is True

    def test_compare_cycles(self, mock_aether_os):
        """Test cross-cycle comparison."""
        agent = ContextAwareAssessmentAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="assessment_agent",
            current_phase=ATOPhase.PHASE6_ASSESSMENT,
            historical_context=HistoricalContext(
                past_cycle_performance=[
                    {"cycle_id": "CYCLE-001", "success_rate": 0.75},
                    {"cycle_id": "CYCLE-002", "success_rate": 0.85},
                ],
            ),
        )

        response = agent.compare_cycles(
            cycle_ids=["CYCLE-001", "CYCLE-002"],
        )

        assert response["success"] is True

    def test_handle_message_assess_missions(self, mock_aether_os):
        """Test message handling for mission assessment."""
        agent = ContextAwareAssessmentAgent(mock_aether_os)

        agent.current_context = AgentContext(
            agent_id="assessment_agent",
            current_phase=ATOPhase.PHASE6_ASSESSMENT,
        )

        response = agent.handle_message(
            sender="orchestrator",
            message_type="assess_missions",
            payload={
                "missions": [
                    {"mission_id": "M-001", "status": "success"},
                ],
                "execution_data": {"objectives_met": 1},
            },
        )

        assert response["success"] is True


def test_agents_integration_phase4():
    """Test ATO Producer and Assessment agents working together."""
    mock_aether_os = Mock()
    mock_aether_os.context_manager = Mock()
    mock_aether_os.performance_evaluator = Mock()
    mock_aether_os.improvement_logger = Mock()
    mock_aether_os.improvement_logger.get_flags_by_cycle.return_value = []
    mock_aether_os.improvement_logger.analyze_patterns.return_value = []

    # Create agents
    ato_producer = ContextAwareATOProducerAgent(mock_aether_os)
    assessment = ContextAwareAssessmentAgent(mock_aether_os)

    # Set up context for Phase 4
    context = AgentContext(
        agent_id="ato_producer_agent",
        current_phase=ATOPhase.PHASE4_ATO_PRODUCTION,
        doctrinal_context=DoctrineContext(
            relevant_procedures=[
                {"content": "Produce ATO with all EMS missions"},
            ],
        ),
        situational_context=SituationalContext(
            active_missions=[
                {"mission_id": "M-001", "mission_type": "EA", "approved": True},
            ],
        ),
    )

    # Step 1: Produce ATO
    ato_producer.current_context = context
    ato_response = ato_producer.produce_ato_ems_annex(
        ew_missions=[
            {"mission_id": "M-001", "mission_type": "EA", "target_id": "THR-001"},
        ],
        frequency_allocations=[
            {"mission_id": "M-001", "frequency_min_mhz": 2000},
        ],
    )

    assert ato_response["success"] is True

    # Step 2: Assess cycle (Phase 6)
    context.agent_id = "assessment_agent"
    context.current_phase = ATOPhase.PHASE6_ASSESSMENT
    assessment.current_context = context

    assessment_response = assessment.assess_mission_effectiveness(
        missions=[
            {"mission_id": "M-001", "status": "success", "mission_type": "EA"},
        ],
    )

    assert assessment_response["success"] is True

    print("\n✅ Phase 4 integration test passed: ATO Producer and Assessment agents executed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
