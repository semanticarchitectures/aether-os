"""
Agent Testing Framework for Aether OS.

Provides controlled testing of individual agents with custom contexts,
messages, and automated response evaluation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from aether_os.agent_context import AgentContext
from aether_os.orchestrator import ATOPhase

logger = logging.getLogger(__name__)


@dataclass
class TestMessage:
    """A message to send to an agent under test."""
    message_type: str
    payload: Dict[str, Any]
    expected_response_criteria: Optional[Dict[str, Any]] = None
    description: str = ""


@dataclass
class TestContext:
    """Context configuration for agent testing."""
    # Override specific context components
    doctrinal_procedures: List[str] = field(default_factory=list)
    threats: List[Dict[str, Any]] = field(default_factory=list)
    assets: List[Dict[str, Any]] = field(default_factory=list)
    missions: List[Dict[str, Any]] = field(default_factory=list)
    historical_lessons: List[str] = field(default_factory=list)

    # Phase context
    phase: Optional[ATOPhase] = None
    task_description: str = ""

    # Size constraints
    max_context_size: int = 32000


@dataclass
class AgentTestScenario:
    """
    Defines a complete test scenario for an agent.

    A scenario includes:
    - Context setup
    - Series of messages/tasks
    - Evaluation criteria
    """
    scenario_id: str
    name: str
    description: str
    agent_id: str

    # Test configuration
    context: TestContext
    messages: List[TestMessage] = field(default_factory=list)

    # Evaluation criteria
    evaluation_criteria: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    tags: List[str] = field(default_factory=list)
    difficulty: str = "medium"  # easy, medium, hard
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentTestResult:
    """Results from executing an agent test."""
    scenario_id: str
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Execution results
    messages_sent: int = 0
    responses_received: int = 0
    execution_time_seconds: float = 0.0

    # Response data
    response_log: List[Dict[str, Any]] = field(default_factory=list)

    # Evaluation results
    evaluation_score: float = 0.0  # 0.0-1.0
    evaluation_feedback: str = ""
    criteria_scores: Dict[str, float] = field(default_factory=dict)

    # Context usage
    context_provided: Optional[AgentContext] = None
    context_utilization: float = 0.0

    # Success/failure
    passed: bool = False
    errors: List[str] = field(default_factory=list)


class AgentTestRunner:
    """
    Executes agent test scenarios.

    Provides controlled environment for testing agent behavior
    with custom contexts and messages.
    """

    def __init__(self, aether_os: Any, evaluator_agent: Any = None):
        """
        Initialize test runner.

        Args:
            aether_os: AetherOS instance
            evaluator_agent: Agent that evaluates responses (optional)
        """
        self.aether_os = aether_os
        self.evaluator_agent = evaluator_agent

        # Test history
        self.test_results: List[AgentTestResult] = []

        logger.info("AgentTestRunner initialized")

    async def run_scenario(
        self,
        scenario: AgentTestScenario,
        agent: Any,
    ) -> AgentTestResult:
        """
        Execute a test scenario on an agent.

        Args:
            scenario: Test scenario to execute
            agent: Agent instance to test

        Returns:
            AgentTestResult with execution and evaluation data
        """
        logger.info(f"Running test scenario: {scenario.name} for {scenario.agent_id}")

        result = AgentTestResult(
            scenario_id=scenario.scenario_id,
            agent_id=scenario.agent_id,
        )

        start_time = datetime.now()

        try:
            # Build custom context for agent
            context = self._build_test_context(scenario.context, agent)
            result.context_provided = context

            # Provide context to agent
            agent.current_context = context
            logger.info(f"Provided test context: {context.total_size()} tokens")

            # Execute test messages
            for msg_idx, test_msg in enumerate(scenario.messages):
                logger.info(
                    f"Sending message {msg_idx + 1}/{len(scenario.messages)}: "
                    f"{test_msg.message_type}"
                )

                # Send message to agent
                response = await self._send_test_message(agent, test_msg)

                # Record response
                result.response_log.append({
                    "message_index": msg_idx,
                    "message_type": test_msg.message_type,
                    "message_payload": test_msg.payload,
                    "response": response,
                    "timestamp": datetime.now().isoformat(),
                })

                result.messages_sent += 1
                if response.get("success"):
                    result.responses_received += 1

            # Calculate context utilization
            if context:
                result.context_utilization = context.get_utilization_rate()

            # Evaluate responses
            if self.evaluator_agent:
                evaluation = await self._evaluate_responses(
                    scenario=scenario,
                    responses=result.response_log,
                    context=context,
                )

                result.evaluation_score = evaluation.get("overall_score", 0.0)
                result.evaluation_feedback = evaluation.get("feedback", "")
                result.criteria_scores = evaluation.get("criteria_scores", {})
                result.passed = evaluation.get("passed", False)
            else:
                # Simple pass/fail based on response success
                result.passed = result.responses_received == result.messages_sent
                result.evaluation_score = (
                    result.responses_received / result.messages_sent
                    if result.messages_sent > 0
                    else 0.0
                )

        except Exception as e:
            logger.error(f"Error running test scenario: {e}", exc_info=True)
            result.errors.append(str(e))
            result.passed = False

        # Calculate execution time
        result.execution_time_seconds = (datetime.now() - start_time).total_seconds()

        # Store result
        self.test_results.append(result)

        logger.info(
            f"Test scenario complete: {scenario.name} | "
            f"Score: {result.evaluation_score:.2f} | "
            f"Passed: {result.passed}"
        )

        return result

    def _build_test_context(
        self,
        test_context: TestContext,
        agent: Any,
    ) -> AgentContext:
        """Build custom context from test configuration."""
        from aether_os.agent_context import (
            AgentContext,
            DoctrineContext,
            SituationalContext,
            HistoricalContext,
            CollaborativeContext,
        )

        context = AgentContext(
            agent_id=agent.agent_id,
            current_phase=test_context.phase,
            current_task=test_context.task_description,
        )

        # Build doctrine context
        context.doctrinal_context = DoctrineContext(
            best_practices=test_context.doctrinal_procedures,
        )

        # Build situational context
        context.situational_context = SituationalContext(
            current_threats=test_context.threats,
            available_assets=test_context.assets,
            active_missions=test_context.missions,
        )

        # Build historical context
        context.historical_context = HistoricalContext(
            lessons_learned=test_context.historical_lessons,
        )

        # Build collaborative context
        context.collaborative_context = CollaborativeContext()

        logger.info(
            f"Built test context: {context.total_size()} tokens "
            f"(max: {test_context.max_context_size})"
        )

        return context

    async def _send_test_message(
        self,
        agent: Any,
        test_message: TestMessage,
    ) -> Dict[str, Any]:
        """Send a test message to the agent."""
        try:
            # Check if agent has message handler
            if not hasattr(agent, 'handle_message'):
                return {
                    "success": False,
                    "error": "Agent does not support message handling",
                }

            # Send message
            response = agent.handle_message(
                from_agent="test_runner",
                message_type=test_message.message_type,
                payload=test_message.payload,
            )

            # Await if coroutine
            import asyncio
            if asyncio.iscoroutine(response):
                response = await response

            return response

        except Exception as e:
            logger.error(f"Error sending test message: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

    async def _evaluate_responses(
        self,
        scenario: AgentTestScenario,
        responses: List[Dict[str, Any]],
        context: AgentContext,
    ) -> Dict[str, Any]:
        """Use evaluator agent to evaluate responses."""
        if not self.evaluator_agent:
            return {
                "overall_score": 0.5,
                "feedback": "No evaluator agent configured",
                "passed": False,
            }

        # Prepare evaluation request
        evaluation_request = {
            "scenario_name": scenario.name,
            "scenario_description": scenario.description,
            "evaluation_criteria": scenario.evaluation_criteria,
            "responses": responses,
            "context_provided": context.to_dict() if context else {},
            "context_utilization": context.get_utilization_rate() if context else 0.0,
        }

        # Send to evaluator agent
        try:
            evaluation = self.evaluator_agent.evaluate_agent_responses(
                evaluation_request
            )

            # Await if coroutine
            import asyncio
            if asyncio.iscoroutine(evaluation):
                evaluation = await evaluation

            return evaluation

        except Exception as e:
            logger.error(f"Error evaluating responses: {e}", exc_info=True)
            return {
                "overall_score": 0.0,
                "feedback": f"Evaluation error: {str(e)}",
                "passed": False,
            }

    def generate_test_report(
        self,
        scenario_id: Optional[str] = None,
    ) -> str:
        """Generate test results report."""
        if scenario_id:
            results = [r for r in self.test_results if r.scenario_id == scenario_id]
        else:
            results = self.test_results

        if not results:
            return "No test results available"

        report = "=" * 80 + "\n"
        report += "AGENT TEST RESULTS\n"
        report += "=" * 80 + "\n\n"

        for result in results:
            report += f"Scenario: {result.scenario_id}\n"
            report += f"Agent: {result.agent_id}\n"
            report += f"Timestamp: {result.timestamp.isoformat()}\n"
            report += f"\n"
            report += f"Messages Sent: {result.messages_sent}\n"
            report += f"Responses Received: {result.responses_received}\n"
            report += f"Execution Time: {result.execution_time_seconds:.2f}s\n"
            report += f"Context Utilization: {result.context_utilization:.1%}\n"
            report += f"\n"
            report += f"Evaluation Score: {result.evaluation_score:.2f}/1.0\n"
            report += f"Passed: {'✓' if result.passed else '✗'}\n"

            if result.criteria_scores:
                report += f"\nCriteria Scores:\n"
                for criterion, score in result.criteria_scores.items():
                    report += f"  {criterion}: {score:.2f}\n"

            if result.evaluation_feedback:
                report += f"\nFeedback:\n{result.evaluation_feedback}\n"

            if result.errors:
                report += f"\nErrors:\n"
                for error in result.errors:
                    report += f"  - {error}\n"

            report += "\n" + "-" * 80 + "\n\n"

        # Summary statistics
        if len(results) > 1:
            avg_score = sum(r.evaluation_score for r in results) / len(results)
            pass_rate = sum(1 for r in results if r.passed) / len(results)

            report += "SUMMARY\n"
            report += "-" * 80 + "\n"
            report += f"Total Tests: {len(results)}\n"
            report += f"Average Score: {avg_score:.2f}\n"
            report += f"Pass Rate: {pass_rate:.1%}\n"

        return report
