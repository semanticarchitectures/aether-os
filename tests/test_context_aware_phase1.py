"""
Unit tests for Phase 1 context-aware components.

Tests:
- LLMClient
- ContextProcessor
- PromptBuilder
- ContextAwareBaseAgent
"""

import pytest
import os
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

from aether_os.llm_client import LLMClient, LLMProvider, LLMResponse
from aether_os.context_processor import ContextProcessor, ProcessedContext
from aether_os.prompt_builder import PromptBuilder, get_task_template
from aether_os.context_aware_agent import ContextAwareBaseAgent
from aether_os.agent_context import AgentContext
from aether_os.orchestrator import ATOPhase


class TestLLMClient:
    """Test LLMClient functionality."""

    def test_initialization(self):
        """Test LLMClient initialization."""
        client = LLMClient(primary_provider=LLMProvider.ANTHROPIC)
        assert client.primary_provider == LLMProvider.ANTHROPIC
        assert client.max_retries == 3

    def test_is_available(self):
        """Test availability check."""
        client = LLMClient()
        # Should return bool
        assert isinstance(client.is_available(), bool)

    def test_get_available_providers(self):
        """Test getting available providers."""
        client = LLMClient()
        providers = client.get_available_providers()
        assert isinstance(providers, list)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_anthropic_initialization(self):
        """Test Anthropic client initialization with API key."""
        with patch('aether_os.llm_client.Anthropic') as mock_anthropic:
            client = LLMClient(primary_provider=LLMProvider.ANTHROPIC)
            # Should attempt to initialize Anthropic
            assert LLMProvider.ANTHROPIC in client.clients or not client.clients

    def test_fallback_without_api_keys(self):
        """Test that client handles missing API keys gracefully."""
        # Clear API keys
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient()
            # Should initialize without errors
            assert client is not None


class TestContextProcessor:
    """Test ContextProcessor functionality."""

    def test_initialization(self):
        """Test ContextProcessor initialization."""
        processor = ContextProcessor()
        assert processor is not None

    def test_format_doctrinal_context(self):
        """Test doctrinal context formatting."""
        processor = ContextProcessor()

        doctrinal = {
            "procedures": ["Follow JCEOI process", "Coordinate with all users"],
            "policies": ["Maintain spectrum discipline"],
            "best_practices": ["Request spectrum early"],
        }

        text, ids = processor._format_doctrinal_context(doctrinal, None)

        assert "DOCTRINAL PROCEDURES" in text
        assert "Follow JCEOI process" in text
        assert len(ids) == 4  # 2 procedures + 1 policy + 1 best practice = 4 total
        assert all(id.startswith("DOC-") for id in ids)

    def test_format_situational_context(self):
        """Test situational context formatting."""
        processor = ContextProcessor()

        situational = {
            "current_threats": [
                {
                    "threat_id": "THR-001",
                    "threat_type": "SA-10",
                    "location": {"lat": 36.0, "lon": 44.0},
                    "priority": "critical",
                }
            ],
            "available_assets": [
                {
                    "asset_id": "AST-001",
                    "platform": "EA-18G",
                    "capability": "Stand-in jamming",
                }
            ],
        }

        text, ids = processor._format_situational_context(situational)

        assert "CURRENT THREATS" in text
        assert "THR-001" in text
        assert "SA-10" in text
        assert "AVAILABLE ASSETS" in text
        assert "EA-18G" in text
        assert "THR-001" in ids
        assert "AST-001" in ids

    def test_token_counting(self):
        """Test token counting."""
        processor = ContextProcessor()

        text = "This is a test sentence for token counting."
        tokens = processor._count_tokens(text)

        assert tokens > 0
        assert isinstance(tokens, int)

    def test_truncate_to_tokens(self):
        """Test text truncation to fit token budget."""
        processor = ContextProcessor()

        text = "This is a long text. " * 100  # Repeat to make it long
        max_tokens = 50

        truncated = processor._truncate_to_tokens(text, max_tokens)

        assert len(truncated) <= len(text)
        truncated_tokens = processor._count_tokens(truncated)
        assert truncated_tokens <= max_tokens * 1.1  # Allow 10% margin

    def test_extract_citations(self):
        """Test citation extraction from response."""
        processor = ContextProcessor()

        response = """Based on [DOC-001] and [THR-001], I recommend using [AST-001]
        to address the threat. This follows [DOC-PROC-002]."""

        citations = processor.extract_citations(response)

        assert "DOC-001" in citations
        assert "THR-001" in citations
        assert "AST-001" in citations
        assert "DOC-PROC-002" in citations
        assert len(citations) == 4

    def test_process_context(self):
        """Test complete context processing."""
        processor = ContextProcessor()

        # Create test context
        context = AgentContext(
            phase=ATOPhase.PHASE3_WEAPONEERING,
            doctrinal_context={
                "procedures": ["Test procedure 1", "Test procedure 2"],
            },
            situational_context={
                "current_threats": [
                    {"threat_id": "THR-001", "threat_type": "SAM"}
                ],
            },
            historical_context={
                "lessons_learned": ["Lesson 1"],
            },
            collaborative_context={},
        )

        processed = processor.process(context, max_tokens=5000)

        assert isinstance(processed, ProcessedContext)
        assert processed.total_tokens > 0
        assert len(processed.element_ids) > 0
        assert processed.doctrinal_context != ""


class TestPromptBuilder:
    """Test PromptBuilder functionality."""

    def test_initialization(self):
        """Test PromptBuilder initialization."""
        builder = PromptBuilder()
        assert builder is not None

    def test_build_system_prompt(self):
        """Test system prompt building."""
        builder = PromptBuilder()

        system_prompt = builder._build_system_prompt("ems_strategy")

        assert "USAF Air Operations Center" in system_prompt
        assert "EMS Strategy Agent" in system_prompt
        assert "doctrine" in system_prompt.lower()

    def test_build_system_prompt_unknown_role(self):
        """Test system prompt with unknown role."""
        builder = PromptBuilder()

        system_prompt = builder._build_system_prompt("unknown_role")

        # Should still contain base prompt
        assert "USAF Air Operations Center" in system_prompt

    def test_build_prompt(self):
        """Test complete prompt building."""
        builder = PromptBuilder()
        processor = ContextProcessor()

        # Create processed context
        context = AgentContext(
            phase=ATOPhase.PHASE3_WEAPONEERING,
            doctrinal_context={"procedures": ["Test procedure"]},
            situational_context={},
            historical_context={},
            collaborative_context={},
        )

        processed = processor.process(context, max_tokens=5000)

        # Build prompt
        system_prompt, user_prompt = builder.build_prompt(
            role="ew_planner",
            task_description="Plan EW missions",
            processed_context=processed,
        )

        assert "EW Planner Agent" in system_prompt
        assert "Plan EW missions" in user_prompt
        assert "DOCTRINAL CONTEXT" in user_prompt
        assert "YOUR TASK" in user_prompt

    def test_build_simple_prompt(self):
        """Test simple prompt building."""
        builder = PromptBuilder()

        system_prompt, user_prompt = builder.build_simple_prompt(
            role="spectrum_manager",
            task="Allocate frequencies",
            context_summary="2 missions, 3 conflicts",
        )

        assert "Spectrum Manager Agent" in system_prompt
        assert "Allocate frequencies" in user_prompt
        assert "2 missions" in user_prompt

    def test_task_templates(self):
        """Test task template formatting."""
        task = get_task_template(
            "develop_strategy",
            objectives="Objective 1\nObjective 2",
            guidance="Commander's guidance here",
            timeline="72 hours",
        )

        assert "Objective 1" in task
        assert "Commander's guidance" in task
        assert "72 hours" in task

    def test_unknown_task_template(self):
        """Test handling of unknown task template."""
        task = get_task_template(
            "unknown_task",
            task_description="Fallback description",
        )

        assert task == "Fallback description" or task == ""


class TestContextAwareAgent(ContextAwareBaseAgent):
    """Concrete test agent for testing."""

    def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """Implement abstract method for testing."""
        return {"success": True, "test": "phase_task"}


class TestContextAwareBaseAgent:
    """Test ContextAwareBaseAgent functionality."""

    @pytest.fixture
    def mock_aether_os(self):
        """Create mock Aether OS."""
        mock = Mock()
        mock.context_manager = Mock()
        mock.performance_evaluator = Mock()
        return mock

    def test_initialization(self, mock_aether_os):
        """Test agent initialization."""
        agent = TestContextAwareAgent(
            agent_id="ems_strategy_agent",  # Use existing agent ID
            aether_os=mock_aether_os,
            role="ems_strategy",
        )

        assert agent.agent_id == "ems_strategy_agent"
        assert agent.role == "ems_strategy"
        assert isinstance(agent.llm_client, LLMClient)
        assert isinstance(agent.context_processor, ContextProcessor)
        assert isinstance(agent.prompt_builder, PromptBuilder)

    def test_fallback_response(self, mock_aether_os):
        """Test fallback response when LLM unavailable."""
        agent = TestContextAwareAgent(
            agent_id="ew_planner_agent",
            aether_os=mock_aether_os,
            role="ew_planner",
        )

        response = agent._fallback_response("Test task")

        assert response["success"] is True
        assert "Test task" in response["content"]
        assert response["fallback_mode"] is True

    def test_get_context_summary(self, mock_aether_os):
        """Test context summary generation."""
        agent = TestContextAwareAgent(
            agent_id="ew_planner_agent",
            aether_os=mock_aether_os,
            role="ew_planner",
        )

        # No context
        summary = agent.get_context_summary()
        assert "No context" in summary

        # With context
        agent.current_context = AgentContext(
            phase=ATOPhase.PHASE3_WEAPONEERING,
            doctrinal_context={"procedures": ["Proc 1", "Proc 2"]},
            situational_context={
                "current_threats": [{"threat_id": "THR-001"}],
                "available_assets": [{"asset_id": "AST-001"}],
            },
            historical_context={"lessons_learned": ["Lesson 1"]},
            collaborative_context={},
        )

        summary = agent.get_context_summary()
        assert "2 doctrinal procedures" in summary
        assert "1 threats" in summary
        assert "1 assets" in summary

    def test_identify_information_gaps(self, mock_aether_os):
        """Test information gap identification."""
        agent = TestContextAwareAgent(
            agent_id="ew_planner_agent",
            aether_os=mock_aether_os,
            role="ew_planner",
        )

        # No context - all missing
        gaps = agent.identify_information_gaps(
            task="Plan missions",
            required_information=["threats", "assets", "spectrum"],
        )
        assert len(gaps) == 3

        # With some context
        agent.current_context = AgentContext(
            phase=ATOPhase.PHASE3_WEAPONEERING,
            doctrinal_context={},
            situational_context={
                "current_threats": [{"threat_id": "THR-001"}],
            },
            historical_context={},
            collaborative_context={},
        )

        gaps = agent.identify_information_gaps(
            task="Plan missions",
            required_information=["threats", "assets", "spectrum"],
        )

        # "threats" should be found, "assets" and "spectrum" missing
        assert "threats" not in gaps
        assert "assets" in gaps
        assert "spectrum" in gaps


def test_integration():
    """Test integration of all Phase 1 components."""
    # Create mock Aether OS
    mock_aether_os = Mock()
    mock_aether_os.context_manager = Mock()
    mock_aether_os.performance_evaluator = Mock()

    # Create agent
    agent = TestContextAwareAgent(
        agent_id="ems_strategy_agent",
        aether_os=mock_aether_os,
        role="ems_strategy",
    )

    # Set context
    agent.current_context = AgentContext(
        phase=ATOPhase.PHASE1_OEG,
        doctrinal_context={
            "procedures": ["Develop EMS strategy", "Consider all threats"],
        },
        situational_context={
            "current_threats": [
                {
                    "threat_id": "THR-001",
                    "threat_type": "SA-10",
                    "location": {"lat": 36.0, "lon": 44.0},
                }
            ],
        },
        historical_context={
            "lessons_learned": ["SA-10 requires standoff jamming"],
        },
        collaborative_context={},
    )

    # Test context processing
    summary = agent.get_context_summary()
    assert "2 doctrinal procedures" in summary
    assert "1 threats" in summary

    # Test without LLM (fallback mode)
    response = agent.generate_with_context(
        task_description="Develop EMS strategy for high-threat environment",
    )

    # Should get fallback response if no LLM available
    assert response["success"] is True
    assert "content" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
