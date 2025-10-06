# Single Agent Testing Guide

This guide explains how to test individual Aether OS agents in isolation, without requiring the full system to be running.

## Overview

Single agent testing allows you to:
- **Test one agent at a time** without system dependencies
- **Use mocked dependencies** for fast, reliable unit tests
- **Use real LLMs** for integration testing
- **Debug agent behavior** in isolation
- **Validate agent responses** with structured assertions

## Available Test Types

### 1. Unit Tests (Mocked Dependencies)
- **Fast execution** (3-5 seconds)
- **No external dependencies** (no LLM API calls)
- **Predictable results** using mocked responses
- **Ideal for CI/CD** and rapid development

### 2. Integration Tests (Real LLM)
- **Real LLM generation** using actual API calls
- **End-to-end validation** of agent behavior
- **Slower execution** (30-60 seconds per agent)
- **Requires API keys** to be configured

## Quick Start

### Test All Agents (Unit Tests)
```bash
# Run unit tests for all agents
python scripts/run_agent_tests.py all --unit

# Run with verbose output
python scripts/run_agent_tests.py all --unit --verbose
```

### Test Single Agent (Unit Tests)
```bash
# Test EMS Strategy Agent
python scripts/run_agent_tests.py ems_strategy --unit

# Test EW Planner Agent  
python scripts/run_agent_tests.py ew_planner --unit

# Test Spectrum Manager Agent
python scripts/run_agent_tests.py spectrum_manager --unit
```

### Test Single Agent (Integration Tests)
```bash
# Test with real LLM (requires API keys)
python scripts/run_agent_tests.py ems_strategy --integration

# Test all agents with real LLM
python scripts/run_agent_tests.py all --integration
```

### Test Both Unit and Integration
```bash
# Run both unit and integration tests
python scripts/run_agent_tests.py ems_strategy --unit --integration
```

## Test Structure

### Unit Test Classes

Each agent has a dedicated test class:

- **`TestEMSStrategyAgent`** - Tests EMS Strategy Agent
- **`TestEWPlannerAgent`** - Tests EW Planner Agent  
- **`TestSpectrumManagerAgent`** - Tests Spectrum Manager Agent

### Test Methods

Each test class includes:

1. **`test_agent_initialization`** - Verifies agent initializes correctly
2. **`test_[method]_with_mock_llm`** - Tests main agent method with mocked LLM
3. **`test_[method]_with_insufficient_context`** - Tests edge cases

### Mock Fixtures

The tests use pytest fixtures for consistent mocking:

- **`mock_llm_client`** - Mocked LLM client with predictable responses
- **`mock_context_processor`** - Mocked context processing
- **`mock_semantic_tracker`** - Mocked semantic tracking
- **`sample_agent_context`** - Sample context data for testing

## Example Test Output

### Unit Test Success
```
🧪 AETHER OS AGENT TEST RUNNER
================================================================================
📋 UNIT TESTS (Mocked Dependencies)
================================================================================
🧪 Running tests for: ems_strategy
📁 Test pattern: tests/test_single_agent.py::TestEMSStrategyAgent
------------------------------------------------------------
tests/test_single_agent.py::TestEMSStrategyAgent::test_agent_initialization PASSED
tests/test_single_agent.py::TestEMSStrategyAgent::test_develop_strategy_with_mock_llm PASSED
tests/test_single_agent.py::TestEMSStrategyAgent::test_strategy_with_insufficient_context PASSED

3 passed in 3.26s

🎉 All tests completed successfully!
```

### Integration Test Success
```
🧪 AETHER OS AGENT TEST RUNNER
================================================================================
🔗 INTEGRATION TESTS (Real LLM)
================================================================================
🔗 Running integration test for: ems_strategy
------------------------------------------------------------
================================================================================
TESTING EMS STRATEGY AGENT
================================================================================
🤖 Testing strategy development...
✅ Strategy development successful!
📊 Result type: <class 'dict'>

Overall: 1/1 tests passed
🎉 All tests passed!
```

## Writing Custom Tests

### Adding New Test Methods

To add a new test method to an existing agent test class:

```python
def test_custom_behavior(self, ems_strategy_agent):
    """Test custom agent behavior."""
    # Mock the response
    mock_response = {"custom_field": "test_value"}
    
    with patch.object(ems_strategy_agent, 'generate_with_context') as mock_generate:
        mock_generate.return_value = mock_response
        
        # Call agent method
        result = ems_strategy_agent.custom_method("test_input")
        
        # Verify results
        assert result is not None
        assert "custom_field" in result
        mock_generate.assert_called_once()
```

### Testing New Agents

To add tests for a new agent:

1. **Create agent test class** in `tests/test_single_agent.py`
2. **Add agent mapping** in `scripts/run_agent_tests.py`
3. **Add integration test** in `scripts/test_single_agent.py`

## Debugging Failed Tests

### Common Issues

1. **Method Signature Mismatch**
   - Check agent method parameters match test calls
   - Verify parameter names and types

2. **Mock Setup Issues**
   - Ensure mocks are properly configured
   - Check that `generate_with_context` is being mocked

3. **Context Structure Changes**
   - Update `sample_agent_context` fixture if context structure changes
   - Verify AgentContext constructor parameters

### Debugging Tips

1. **Use verbose output** (`--verbose`) to see detailed test execution
2. **Run single test method** using pytest directly:
   ```bash
   python -m pytest tests/test_single_agent.py::TestEMSStrategyAgent::test_agent_initialization -v
   ```
3. **Add debug prints** in test methods to inspect values
4. **Check agent logs** for error messages during integration tests

## Benefits

### For Development
- **Fast feedback loop** during agent development
- **Isolated testing** without system complexity
- **Predictable test environment** with mocked dependencies

### For CI/CD
- **Reliable unit tests** that don't depend on external APIs
- **Fast execution** suitable for continuous integration
- **Clear pass/fail criteria** for automated testing

### For Debugging
- **Focused testing** of individual agent behavior
- **Controlled inputs** for reproducing issues
- **Detailed assertions** for validating outputs

## Integration with Full System

Single agent tests complement full system testing:

- **Unit tests** validate individual agent logic
- **Integration tests** verify agent-LLM interaction
- **System tests** validate agent coordination and workflows

Use single agent tests during development, then run full system tests for end-to-end validation.
