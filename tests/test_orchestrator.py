"""
Tests for ATO cycle orchestrator
"""

import pytest
from datetime import datetime, timedelta
from aether_os.orchestrator import ATOCycleOrchestrator, ATOPhase


def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    orchestrator = ATOCycleOrchestrator()

    assert orchestrator.current_cycle is None
    assert len(orchestrator.phase_definitions) == 6


def test_start_new_cycle():
    """Test starting a new ATO cycle."""
    orchestrator = ATOCycleOrchestrator()

    cycle = orchestrator.start_new_cycle()

    assert cycle is not None
    assert cycle.cycle_id == "ATO-0001"
    assert cycle.status == "active"
    assert cycle.current_phase == ATOPhase.PHASE1_OEG


def test_get_current_phase():
    """Test getting current phase."""
    orchestrator = ATOCycleOrchestrator()
    orchestrator.start_new_cycle()

    current_phase = orchestrator.get_current_phase()

    assert current_phase == ATOPhase.PHASE1_OEG


def test_get_active_agents():
    """Test getting active agents for current phase."""
    orchestrator = ATOCycleOrchestrator()
    orchestrator.start_new_cycle()

    active_agents = orchestrator.get_active_agents()

    assert "ems_strategy_agent" in active_agents
    assert len(active_agents) == 1  # Only EMS Strategy in Phase 1


def test_phase_definitions():
    """Test that all phases are defined with correct timing."""
    orchestrator = ATOCycleOrchestrator()

    # Verify all 6 phases exist
    assert len(orchestrator.phase_definitions) == 6

    # Verify total duration is 72 hours
    total_duration = sum(
        phase_def.duration_hours
        for phase_def in orchestrator.phase_definitions.values()
    )

    assert total_duration == 72


def test_record_output():
    """Test recording cycle outputs."""
    orchestrator = ATOCycleOrchestrator()
    orchestrator.start_new_cycle()

    orchestrator.record_output("test_output", {"data": "value"})

    assert "test_output" in orchestrator.current_cycle.outputs
    assert orchestrator.current_cycle.outputs["test_output"] == {"data": "value"}


def test_get_cycle_summary():
    """Test getting cycle summary."""
    orchestrator = ATOCycleOrchestrator()
    cycle = orchestrator.start_new_cycle()

    summary = orchestrator.get_cycle_summary()

    assert summary["cycle_id"] == cycle.cycle_id
    assert summary["status"] == "active"
    assert summary["current_phase"] == ATOPhase.PHASE1_OEG.value
