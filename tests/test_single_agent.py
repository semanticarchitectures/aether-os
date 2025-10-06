#!/usr/bin/env python3
"""
Single Agent Unit Tests for Aether OS.

Test individual agents in isolation without requiring the full system.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from aether_os.llm_client import LLMClient, LLMResponse, LLMProvider
from aether_os.context_processor import ContextProcessor, ProcessedContext
from aether_os.prompt_builder import PromptBuilder
from aether_os.semantic_context_tracker import SemanticContextTracker
from aether_os.agent_context import AgentContext, DoctrineContext, SituationalContext
from aether_os.orchestrator import ATOPhase
from agents.context_aware_ems_strategy_agent import ContextAwareEMSStrategyAgent, EMSStrategyResponse
from agents.context_aware_ew_planner_agent import ContextAwareEWPlannerAgent, EWMissionPlanResponse
from agents.context_aware_spectrum_manager_agent import ContextAwareSpectrumManagerAgent, SpectrumAllocationResponse


class TestSingleAgent:
    """Base class for single agent testing."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = Mock()
        
        # Mock successful response
        mock_response = LLMResponse(
            content='{"test": "response"}',
            model="claude-sonnet-4-20250514",
            provider=LLMProvider.ANTHROPIC,
            tokens_used=100,
            finish_reason="stop"
        )
        client.generate.return_value = mock_response
        
        return client
    
    @pytest.fixture
    def mock_context_processor(self):
        """Create a mock context processor."""
        processor = Mock()

        # Mock processed context
        mock_processed = ProcessedContext(
            doctrinal_context="Mock doctrine",
            situational_context="Mock situation",
            historical_context="Mock history",
            collaborative_context="Mock collaboration",
            total_tokens=300,
            element_ids=["DOC-001", "THR-001", "AST-001"],
            truncated=False
        )
        processor.process_context.return_value = mock_processed
        processor.extract_citations.return_value = ["DOC-001", "THR-001"]

        return processor
    
    @pytest.fixture
    def mock_semantic_tracker(self):
        """Create a mock semantic tracker."""
        tracker = Mock()

        # Mock tracking results
        mock_usage = Mock()
        mock_usage.cited_elements = ["DOC-001", "THR-001"]
        mock_usage.semantic_matches = []
        mock_usage.utilization_rate = 0.67

        mock_validation = Mock()
        mock_validation.valid_citations = ["DOC-001", "THR-001"]
        mock_validation.invalid_citations = []
        mock_validation.accuracy = 1.0

        tracker.track_usage.return_value = mock_usage
        tracker.validate_citations.return_value = mock_validation

        return tracker
    
    @pytest.fixture
    def sample_agent_context(self):
        """Create sample agent context."""
        doctrine = DoctrineContext(
            relevant_procedures=[
                {"id": "DOC-PROC-001", "content": "Test procedure", "source": "Test doctrine"}
            ],
            best_practices=["Test best practice"]
        )

        situational = SituationalContext(
            current_threats=[
                {"id": "THR-001", "type": "SAM", "location": [36.5, 44.5], "priority": "critical"}
            ],
            available_assets=[
                {"id": "AST-001", "type": "EA-18G", "status": "available"}
            ],
            spectrum_status={"allocations": []}
        )

        return AgentContext(
            agent_id="test_agent",
            current_phase=ATOPhase.PHASE1_OEG,
            doctrinal_context=doctrine,
            situational_context=situational,
            historical_context=None,
            collaborative_context=None
        )


class TestEMSStrategyAgent(TestSingleAgent):
    """Test EMS Strategy Agent in isolation."""
    
    @pytest.fixture
    def ems_strategy_agent(self, mock_llm_client, mock_context_processor, mock_semantic_tracker):
        """Create EMS Strategy Agent with mocked dependencies."""
        agent = ContextAwareEMSStrategyAgent("test_ems_strategy")
        agent.llm_client = mock_llm_client
        agent.context_processor = mock_context_processor
        agent.semantic_tracker = mock_semantic_tracker
        return agent
    
    def test_agent_initialization(self, ems_strategy_agent):
        """Test agent initializes correctly."""
        # The agent uses its own ID generation, so check it exists
        assert ems_strategy_agent.agent_id is not None
        assert ems_strategy_agent.role == "ems_strategy"
        assert hasattr(ems_strategy_agent, 'llm_client')
        assert hasattr(ems_strategy_agent, 'context_processor')
    
    def test_develop_strategy_with_mock_llm(self, ems_strategy_agent, sample_agent_context):
        """Test strategy development with mocked LLM response."""
        # Mock LLM to return valid EMSStrategyResponse JSON
        mock_strategy_response = {
            "strategy_summary": "Test EMS strategy",
            "objectives": ["Neutralize threats", "Protect forces"],
            "threat_considerations": ["SA-10 at critical location"],
            "resource_requirements": ["EA-18G Growler"],
            "timeline": "Execute during Phase 1-2",
            "context_citations": ["DOC-PROC-001", "THR-001"],
            "doctrine_citations": ["JP 3-13.1"],
            "information_gaps": ["Missing commander guidance"],
            "confidence": 0.8
        }

        # Mock the LLM response
        mock_llm_response = LLMResponse(
            content=str(mock_strategy_response).replace("'", '"'),
            model="claude-sonnet-4-20250514",
            provider=LLMProvider.ANTHROPIC,
            tokens_used=150,
            finish_reason="stop"
        )

        # Set up the mock to return our response
        ems_strategy_agent.llm_client.generate.return_value = mock_llm_response

        # Mock the context-aware generation method directly
        with patch.object(ems_strategy_agent, 'generate_with_context') as mock_generate:
            mock_generate.return_value = mock_strategy_response

            # Test strategy development
            result = ems_strategy_agent.develop_strategy(
                mission_objectives=["Neutralize threats", "Protect forces"],
                commanders_guidance="Test guidance",
                timeline="Test timeline"
            )

            # Verify results
            assert result is not None
            assert isinstance(result, dict)
            assert "strategy_summary" in result

            # Verify the mock was called
            mock_generate.assert_called_once()
    
    def test_strategy_with_insufficient_context(self, ems_strategy_agent):
        """Test strategy development with minimal context."""
        # Mock a simple response for insufficient context
        mock_response = {
            "strategy_summary": "Limited strategy due to insufficient context",
            "objectives": ["Basic objective"],
            "threat_considerations": [],
            "resource_requirements": [],
            "timeline": "Unknown",
            "context_citations": [],
            "doctrine_citations": [],
            "information_gaps": ["All context missing"],
            "confidence": 0.1
        }

        # Mock the context-aware generation method
        with patch.object(ems_strategy_agent, 'generate_with_context') as mock_generate:
            mock_generate.return_value = mock_response

            # Should still work but with lower confidence
            result = ems_strategy_agent.develop_strategy(
                mission_objectives=["Test objective"],
                commanders_guidance="Test",
                timeline="Test"
            )

            assert result is not None
            assert isinstance(result, dict)
            mock_generate.assert_called_once()


class TestEWPlannerAgent(TestSingleAgent):
    """Test EW Planner Agent in isolation."""
    
    @pytest.fixture
    def ew_planner_agent(self, mock_llm_client, mock_context_processor, mock_semantic_tracker):
        """Create EW Planner Agent with mocked dependencies."""
        agent = ContextAwareEWPlannerAgent("test_ew_planner")
        agent.llm_client = mock_llm_client
        agent.context_processor = mock_context_processor
        agent.semantic_tracker = mock_semantic_tracker
        return agent
    
    def test_plan_missions_with_mock_llm(self, ew_planner_agent, sample_agent_context):
        """Test mission planning with mocked LLM response."""
        # Mock LLM to return valid EWMissionPlanResponse JSON
        mock_mission_response = {
            "missions": [
                {
                    "mission_id": "EW-001",
                    "target_id": "THR-001",
                    "asset_id": "AST-001",
                    "mission_type": "Stand-in Jamming",
                    "toa": "H+1",
                    "coordination_notes": "Test coordination"
                }
            ],
            "asset_assignments": {"AST-001": "THR-001"},
            "frequency_requests": ["S-band jamming frequencies"],
            "fratricide_checks": ["No conflicts identified"],
            "coordination_requirements": ["Coordinate with strike package"],
            "context_citations": ["DOC-PROC-001", "THR-001"],
            "doctrine_citations": ["AFI 10-703"],
            "information_gaps": ["Missing threat frequencies"],
            "confidence": 0.85
        }
        
        # Mock the context-aware generation method directly
        with patch.object(ew_planner_agent, 'generate_with_context') as mock_generate:
            mock_generate.return_value = mock_mission_response

            # Test mission planning
            result = ew_planner_agent.plan_missions(
                mission_type="SEAD",
                targets=["THR-001"],
                timeframe="H to H+4"
            )

            # Verify results
            assert result is not None
            assert isinstance(result, dict)
            assert "missions" in result

            # Verify the mock was called
            mock_generate.assert_called_once()


class TestSpectrumManagerAgent(TestSingleAgent):
    """Test Spectrum Manager Agent in isolation."""
    
    @pytest.fixture
    def spectrum_manager_agent(self, mock_llm_client, mock_context_processor, mock_semantic_tracker):
        """Create Spectrum Manager Agent with mocked dependencies."""
        agent = ContextAwareSpectrumManagerAgent("test_spectrum_manager")
        agent.llm_client = mock_llm_client
        agent.context_processor = mock_context_processor
        agent.semantic_tracker = mock_semantic_tracker
        return agent
    
    def test_allocate_frequencies_with_mock_llm(self, spectrum_manager_agent, sample_agent_context):
        """Test frequency allocation with mocked LLM response."""
        # Mock LLM to return valid SpectrumAllocationResponse JSON
        mock_allocation_response = {
            "allocations": [
                {
                    "mission_id": "EW-001",
                    "frequency_min_mhz": 3000.0,
                    "frequency_max_mhz": 3500.0,
                    "start_time": "H-1",
                    "end_time": "H+2",
                    "notes": "Test allocation"
                }
            ],
            "conflicts_identified": ["No conflicts"],
            "deconfliction_actions": ["Frequency separation applied"],
            "coordination_required": ["Notify friendly radar"],
            "jceoi_compliance": True,
            "context_citations": ["DOC-PROC-001"],
            "doctrine_citations": ["JCEOI"],
            "information_gaps": ["Missing host nation coordination"],
            "confidence": 0.9
        }
        
        # Mock the context-aware generation method directly
        with patch.object(spectrum_manager_agent, 'generate_with_context') as mock_generate:
            mock_generate.return_value = mock_allocation_response

            # Test frequency allocation
            result = spectrum_manager_agent.allocate_frequencies(
                requests=[{"mission_id": "EW-001", "frequency_band": "S-band", "purpose": "jamming"}]
            )

            # Verify results
            assert result is not None
            assert isinstance(result, dict)
            assert "allocations" in result

            # Verify the mock was called
            mock_generate.assert_called_once()


# Utility functions for running individual agent tests
def test_single_ems_strategy_agent():
    """Run only EMS Strategy Agent tests."""
    pytest.main(["-v", "tests/test_single_agent.py::TestEMSStrategyAgent"])


def test_single_ew_planner_agent():
    """Run only EW Planner Agent tests."""
    pytest.main(["-v", "tests/test_single_agent.py::TestEWPlannerAgent"])


def test_single_spectrum_manager_agent():
    """Run only Spectrum Manager Agent tests."""
    pytest.main(["-v", "tests/test_single_agent.py::TestSpectrumManagerAgent"])


if __name__ == "__main__":
    # Run all single agent tests
    pytest.main(["-v", __file__])
