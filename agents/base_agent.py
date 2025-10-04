"""
Base Agent for Aether OS.

Provides common functionality for all AOC agents including doctrinal procedure
execution, timing tracking, and process improvement flagging.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from aether_os.access_control import AgentAccessProfile, AGENT_PROFILES
from aether_os.process_improvement import ProcessImprovementLogger, InefficencyType
from aether_os.agent_context import AgentContext

logger = logging.getLogger(__name__)


class BaseAetherAgent(ABC):
    """
    Abstract base class for all Aether OS agents.

    Provides common functionality:
    - Doctrinal procedure execution with timing
    - Process improvement flagging
    - Human escalation
    - Event handling
    """

    def __init__(
        self,
        agent_id: str,
        aether_os: Any,
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Agent identifier (must exist in AGENT_PROFILES)
            aether_os: Reference to main AetherOS instance
        """
        if agent_id not in AGENT_PROFILES:
            raise ValueError(f"Unknown agent ID: {agent_id}")

        self.agent_id = agent_id
        self.aether_os = aether_os
        self.profile: AgentAccessProfile = AGENT_PROFILES[agent_id]

        # State
        self.is_active = False
        self.current_tasks: Dict[str, Any] = {}
        self.current_context: Optional[AgentContext] = None

        logger.info(f"Initialized {self.__class__.__name__} ({agent_id})")

    @abstractmethod
    async def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """
        Execute tasks for a specific ATO phase.

        Args:
            phase: ATO phase
            cycle_id: ATO cycle ID

        Returns:
            Dictionary of outputs/results
        """
        pass

    def execute_doctrinal_procedure(
        self,
        procedure_name: str,
        procedure_fn: callable,
        expected_time_hours: float,
        cycle_id: str,
        phase: str,
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute a doctrinal procedure with timing tracking.

        Wraps procedure execution to track timing and flag inefficiencies
        if execution takes significantly longer than expected.

        Args:
            procedure_name: Name of the procedure
            procedure_fn: Function implementing the procedure
            expected_time_hours: Expected execution time in hours
            cycle_id: Current ATO cycle ID
            phase: Current phase
            *args, **kwargs: Arguments to pass to procedure_fn

        Returns:
            Result from procedure_fn
        """
        logger.info(
            f"[{self.agent_id}] Starting procedure: {procedure_name} "
            f"(expected: {expected_time_hours:.2f}h)"
        )

        start_time = datetime.now()

        try:
            # Pass cycle_id to procedure if not already in kwargs
            if 'cycle_id' not in kwargs:
                kwargs['cycle_id'] = cycle_id
            result = procedure_fn(*args, **kwargs)

            execution_time_hours = (datetime.now() - start_time).total_seconds() / 3600

            logger.info(
                f"[{self.agent_id}] Completed procedure: {procedure_name} "
                f"(actual: {execution_time_hours:.2f}h)"
            )

            # Flag if execution time exceeds expected by >30%
            if execution_time_hours > expected_time_hours * 1.3:
                time_wasted = execution_time_hours - expected_time_hours

                self.aether_os.improvement_logger.flag_inefficiency(
                    ato_cycle_id=cycle_id,
                    phase=phase,
                    agent_id=self.agent_id,
                    workflow_name=procedure_name,
                    inefficiency_type=InefficencyType.TIMING_CONSTRAINT,
                    description=(
                        f"Procedure '{procedure_name}' took {execution_time_hours:.2f}h "
                        f"vs expected {expected_time_hours:.2f}h "
                        f"({((execution_time_hours/expected_time_hours - 1) * 100):.1f}% over)"
                    ),
                    time_wasted_hours=time_wasted,
                    suggested_improvement=(
                        f"Adjust doctrine timeline for '{procedure_name}' or "
                        f"identify automation opportunities"
                    ),
                    severity="medium" if time_wasted < 2 else "high",
                )

            return result

        except Exception as e:
            logger.error(
                f"[{self.agent_id}] Error in procedure {procedure_name}: {e}",
                exc_info=True,
            )
            raise

    def flag_information_gap(
        self,
        workflow_name: str,
        missing_information: str,
        cycle_id: str,
        phase: str,
    ) -> None:
        """
        Flag an information gap encountered during execution.

        Args:
            workflow_name: Name of the workflow
            missing_information: Description of missing information
            cycle_id: ATO cycle ID
            phase: Current phase
        """
        self.aether_os.improvement_logger.flag_inefficiency(
            ato_cycle_id=cycle_id,
            phase=phase,
            agent_id=self.agent_id,
            workflow_name=workflow_name,
            inefficiency_type=InefficencyType.INFORMATION_GAP,
            description=f"Missing information: {missing_information}",
            suggested_improvement=(
                f"Grant agent direct access to: {missing_information}"
            ),
            severity="medium",
        )

    def flag_redundant_coordination(
        self,
        workflow_name: str,
        coordination_description: str,
        time_wasted_hours: float,
        cycle_id: str,
        phase: str,
    ) -> None:
        """
        Flag redundant coordination steps.

        Args:
            workflow_name: Name of the workflow
            coordination_description: Description of redundant coordination
            time_wasted_hours: Time wasted on coordination
            cycle_id: ATO cycle ID
            phase: Current phase
        """
        self.aether_os.improvement_logger.flag_inefficiency(
            ato_cycle_id=cycle_id,
            phase=phase,
            agent_id=self.agent_id,
            workflow_name=workflow_name,
            inefficiency_type=InefficencyType.REDUNDANT_COORDINATION,
            description=coordination_description,
            time_wasted_hours=time_wasted_hours,
            suggested_improvement="Consolidate approval steps or implement automated coordination",
            severity="medium" if time_wasted_hours < 1 else "high",
        )

    def escalate_for_human_decision(
        self,
        decision_type: str,
        context: Dict[str, Any],
        reason: str,
    ) -> Dict[str, Any]:
        """
        Escalate a decision to human operator.

        Args:
            decision_type: Type of decision needed
            context: Decision context
            reason: Reason for escalation

        Returns:
            Human decision (simulated in prototype)
        """
        logger.warning(
            f"[{self.agent_id}] HUMAN ESCALATION REQUIRED: {decision_type}\n"
            f"Reason: {reason}\n"
            f"Context: {context}"
        )

        # In production, this would interface with a human operator
        # For prototype, return a simulated decision
        return {
            "approved": True,
            "decision": "simulated_approval",
            "human_operator": "SIM-OPERATOR",
            "notes": "Simulated human decision for prototype",
        }

    def query_doctrine(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> list:
        """
        Query doctrine knowledge base.

        Args:
            query: Natural language query
            filters: Optional metadata filters

        Returns:
            List of matching doctrine passages
        """
        from aether_os.access_control import InformationCategory

        result = self.aether_os.query_information(
            agent_id=self.agent_id,
            category=InformationCategory.DOCTRINE,
            query_params={
                "query": query,
                "filters": filters,
            },
        )

        if result["success"]:
            return result["data"]
        else:
            logger.error(f"Doctrine query failed: {result.get('error')}")
            return []

    def handle_message(
        self,
        from_agent: str,
        message_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle a message from another agent or system.

        Args:
            from_agent: Sending agent ID
            message_type: Type of message
            payload: Message payload

        Returns:
            Response dictionary
        """
        logger.info(
            f"[{self.agent_id}] Received message from {from_agent}: {message_type}"
        )

        # Dispatch to specific handler if it exists
        handler_name = f"_handle_{message_type}"
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            return handler(from_agent, payload)

        # Default response
        return {
            "success": True,
            "message": f"Message received but no specific handler for {message_type}",
        }

    def request_context(
        self,
        task_description: str,
        max_context_size: int = 32000,
    ) -> AgentContext:
        """
        Request context window from AetherOS.

        Args:
            task_description: Description of current task
            max_context_size: Maximum context size in tokens

        Returns:
            AgentContext with relevant information
        """
        self.current_context = self.aether_os.build_agent_context(
            agent_id=self.agent_id,
            current_task=task_description,
            max_context_size=max_context_size,
        )

        logger.info(
            f"[{self.agent_id}] Received context: {self.current_context.total_size()} tokens"
        )

        return self.current_context

    def reference_context_item(self, item_id: str) -> None:
        """
        Mark a context item as referenced/used.

        Args:
            item_id: Identifier of the context item
        """
        if self.current_context:
            self.current_context.add_referenced_item(item_id)

    def finalize_context_usage(self, result: Dict[str, Any]) -> None:
        """
        Finalize context usage tracking after task completion.

        Args:
            result: Task result dictionary
        """
        if self.current_context:
            usage_stats = self.aether_os.track_context_usage(
                agent_id=self.agent_id,
                context=self.current_context,
                result=result,
            )

            logger.debug(
                f"[{self.agent_id}] Context utilization: "
                f"{usage_stats['utilization_rate']:.1%}"
            )

    def on_activate(self) -> None:
        """Called when agent is activated."""
        self.is_active = True
        logger.info(f"[{self.agent_id}] Activated")

    def on_deactivate(self) -> None:
        """Called when agent is deactivated."""
        self.is_active = False
        self.current_context = None  # Clear context on deactivation
        logger.info(f"[{self.agent_id}] Deactivated")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.agent_id}, active={self.is_active})"
