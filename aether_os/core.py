"""
Core Aether OS implementation.

Main AetherOS class that integrates all subsystems and provides the primary
interface for agent orchestration and coordination.
"""

from typing import Dict, List, Optional, Any
import asyncio
import logging

from aether_os.access_control import (
    AgentAccessProfile,
    InformationCategory,
    AGENT_PROFILES,
)
from aether_os.authorization import AOCAuthorizationEngine, AOCAuthorizationContext
from aether_os.information_broker import AOCInformationBroker
from aether_os.process_improvement import ProcessImprovementLogger
from aether_os.orchestrator import ATOCycleOrchestrator, ATOPhase
from aether_os.doctrine_kb import DoctrineKnowledgeBase
from aether_os.context_manager import AgentContextManager
from aether_os.performance_evaluator import AgentPerformanceEvaluator
from aether_os.context_feedback import ContextPerformanceFeedback

logger = logging.getLogger(__name__)


class AetherOS:
    """
    Main Aether OS class.

    Provides the AI-mediated operating system layer between USAF AOC personnel
    and organizational assets for Electromagnetic Spectrum Operations.
    """

    def __init__(
        self,
        doctrine_kb_path: Optional[str] = None,
        opa_url: Optional[str] = None,
    ):
        """
        Initialize Aether OS.

        Args:
            doctrine_kb_path: Path to doctrine knowledge base
            opa_url: URL of Open Policy Agent server
        """
        logger.info("Initializing Aether OS...")

        # Initialize subsystems
        self.doctrine_kb = DoctrineKnowledgeBase(persist_directory=doctrine_kb_path)
        self.authorization = AOCAuthorizationEngine(opa_url=opa_url)
        self.information_broker = AOCInformationBroker(doctrine_kb=self.doctrine_kb)
        self.improvement_logger = ProcessImprovementLogger()
        self.orchestrator = ATOCycleOrchestrator()

        # Context and performance subsystems
        self.context_manager = AgentContextManager(
            doctrine_kb=self.doctrine_kb,
            information_broker=self.information_broker,
        )
        self.performance_evaluator = AgentPerformanceEvaluator(aether_os=self)
        self.context_feedback = ContextPerformanceFeedback(
            context_manager=self.context_manager,
            performance_evaluator=self.performance_evaluator,
        )

        # Agent registry
        self.registered_agents: Dict[str, Any] = {}
        self.active_agents: Dict[str, Any] = {}

        # Event handlers
        self._event_handlers: Dict[str, List[callable]] = {}

        logger.info("Aether OS initialized successfully")

    async def start(self) -> None:
        """Start Aether OS and begin ATO cycle monitoring."""
        logger.info("Starting Aether OS...")

        # Register phase callbacks
        for phase in ATOPhase:
            self.orchestrator.register_phase_callback(
                phase, self._on_phase_transition
            )

        # Start monitoring
        await self.orchestrator.start_monitoring()

        logger.info("Aether OS started")

    async def stop(self) -> None:
        """Stop Aether OS and cleanup resources."""
        logger.info("Stopping Aether OS...")

        # Stop monitoring
        await self.orchestrator.stop_monitoring()

        # Deactivate all agents
        for agent_id in list(self.active_agents.keys()):
            await self.deactivate_agent(agent_id)

        logger.info("Aether OS stopped")

    def register_agent(self, agent_id: str, agent_instance: Any) -> bool:
        """
        Register an agent with Aether OS.

        Args:
            agent_id: Agent identifier (must match AGENT_PROFILES)
            agent_instance: Agent instance

        Returns:
            True if successful, False otherwise
        """
        if agent_id not in AGENT_PROFILES:
            logger.error(f"Unknown agent ID: {agent_id}")
            return False

        if agent_id in self.registered_agents:
            logger.warning(f"Agent {agent_id} already registered")
            return False

        self.registered_agents[agent_id] = agent_instance
        logger.info(f"Registered agent: {agent_id}")

        return True

    async def activate_agent(self, agent_id: str) -> bool:
        """
        Activate an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.registered_agents:
            logger.error(f"Cannot activate unregistered agent: {agent_id}")
            return False

        if agent_id in self.active_agents:
            logger.warning(f"Agent {agent_id} already active")
            return True

        agent = self.registered_agents[agent_id]
        self.active_agents[agent_id] = agent

        # Notify agent of activation
        if hasattr(agent, 'on_activate'):
            try:
                if asyncio.iscoroutinefunction(agent.on_activate):
                    await agent.on_activate()
                else:
                    agent.on_activate()
            except Exception as e:
                logger.error(f"Error activating agent {agent_id}: {e}", exc_info=True)

        logger.info(f"Activated agent: {agent_id}")
        return True

    async def deactivate_agent(self, agent_id: str) -> bool:
        """
        Deactivate an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if successful, False otherwise
        """
        if agent_id not in self.active_agents:
            logger.warning(f"Agent {agent_id} not active")
            return True

        agent = self.active_agents[agent_id]

        # Notify agent of deactivation
        if hasattr(agent, 'on_deactivate'):
            try:
                if asyncio.iscoroutinefunction(agent.on_deactivate):
                    await agent.on_deactivate()
                else:
                    agent.on_deactivate()
            except Exception as e:
                logger.error(f"Error deactivating agent {agent_id}: {e}", exc_info=True)

        del self.active_agents[agent_id]

        logger.info(f"Deactivated agent: {agent_id}")
        return True

    def _on_phase_transition(self, phase: ATOPhase, cycle: Any) -> None:
        """
        Handle phase transition.

        Activates/deactivates agents based on phase.
        """
        logger.info(f"Phase transition to {phase.value}")

        # Get agents that should be active in this phase
        phase_def = self.orchestrator.phase_definitions[phase]
        required_agents = set(phase_def.active_agents)
        current_agents = set(self.active_agents.keys())

        # Deactivate agents that shouldn't be active
        to_deactivate = current_agents - required_agents
        for agent_id in to_deactivate:
            asyncio.create_task(self.deactivate_agent(agent_id))

        # Activate agents that should be active
        to_activate = required_agents - current_agents
        for agent_id in to_activate:
            if agent_id in self.registered_agents:
                asyncio.create_task(self.activate_agent(agent_id))

    def query_information(
        self,
        agent_id: str,
        category: InformationCategory,
        query_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Query information on behalf of an agent.

        Enforces access control and sanitization.

        Args:
            agent_id: ID of agent making the request
            category: Information category
            query_params: Query parameters

        Returns:
            Query results or error
        """
        if agent_id not in AGENT_PROFILES:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_id}",
            }

        agent_profile = AGENT_PROFILES[agent_id]
        current_phase = self.orchestrator.get_current_phase()

        return self.information_broker.query(
            agent_profile=agent_profile,
            category=category,
            query_params=query_params,
            current_phase=current_phase.value if current_phase else None,
        )

    def authorize_action(
        self,
        agent_id: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Authorize an agent action.

        Args:
            agent_id: ID of agent requesting authorization
            action: Action to authorize
            context: Additional context for authorization

        Returns:
            True if authorized, False otherwise
        """
        if agent_id not in AGENT_PROFILES:
            logger.error(f"Unknown agent: {agent_id}")
            return False

        agent_profile = AGENT_PROFILES[agent_id]
        current_phase = self.orchestrator.get_current_phase()

        auth_context = AOCAuthorizationContext(
            agent_profile=agent_profile,
            action=action,
            current_phase=current_phase,
            additional_context=context or {},
        )

        decision = self.authorization.can_agent_act(auth_context)

        if decision.authorized:
            logger.info(f"Action authorized: agent={agent_id}, action={action}")
        else:
            logger.warning(
                f"Action denied: agent={agent_id}, action={action}, "
                f"reason={decision.reason}"
            )

        return decision.authorized

    async def send_agent_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Send a message from one agent to another.

        Args:
            from_agent: Sending agent ID
            to_agent: Receiving agent ID
            message_type: Type of message
            payload: Message payload

        Returns:
            Response from receiving agent
        """
        if to_agent not in self.active_agents:
            logger.error(f"Cannot send message: agent {to_agent} not active")
            return {"success": False, "error": f"Agent {to_agent} not active"}

        receiver = self.active_agents[to_agent]

        if not hasattr(receiver, 'handle_message'):
            logger.error(f"Agent {to_agent} cannot handle messages")
            return {"success": False, "error": f"Agent {to_agent} cannot handle messages"}

        try:
            logger.info(
                f"Routing message: {from_agent} -> {to_agent} (type: {message_type})"
            )

            response = receiver.handle_message(from_agent, message_type, payload)

            if asyncio.iscoroutine(response):
                response = await response

            return response

        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def broadcast_to_agents(
        self,
        message_type: str,
        payload: Dict[str, Any],
        filter_phase: bool = True,
    ) -> Dict[str, Any]:
        """
        Broadcast a message to all active agents.

        Args:
            message_type: Type of message
            payload: Message payload
            filter_phase: Only send to agents active in current phase

        Returns:
            Dictionary mapping agent_id to response
        """
        if filter_phase:
            target_agents = set(self.orchestrator.get_active_agents())
        else:
            target_agents = set(self.active_agents.keys())

        responses = {}

        for agent_id in target_agents:
            if agent_id in self.active_agents:
                response = await self.send_agent_message(
                    from_agent="system",
                    to_agent=agent_id,
                    message_type=message_type,
                    payload=payload,
                )
                responses[agent_id] = response

        return responses

    def start_ato_cycle(self) -> str:
        """
        Start a new ATO cycle.

        Returns:
            Cycle ID
        """
        cycle = self.orchestrator.start_new_cycle()
        logger.info(f"Started ATO cycle: {cycle.cycle_id}")
        return cycle.cycle_id

    def get_current_cycle_id(self) -> Optional[str]:
        """Get current ATO cycle ID."""
        if self.orchestrator.current_cycle:
            return self.orchestrator.current_cycle.cycle_id
        return None

    def get_process_improvement_report(self) -> str:
        """Get process improvement report."""
        return self.improvement_logger.generate_report()

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status.

        Returns:
            Dictionary with system status information
        """
        current_phase = self.orchestrator.get_current_phase()

        return {
            "registered_agents": list(self.registered_agents.keys()),
            "active_agents": list(self.active_agents.keys()),
            "current_cycle": self.orchestrator.get_cycle_summary(),
            "current_phase": current_phase.value if current_phase else None,
            "doctrine_kb_documents": self.doctrine_kb.count_documents(),
            "process_improvement_stats": self.improvement_logger.get_summary_statistics(),
        }

    def build_agent_context(
        self,
        agent_id: str,
        current_task: str,
        max_context_size: int = 32000,
    ):
        """
        Build context window for an agent.

        Args:
            agent_id: Agent identifier
            current_task: Current task description
            max_context_size: Maximum context size in tokens

        Returns:
            AgentContext with all relevant information
        """
        current_phase = self.orchestrator.get_current_phase()

        return self.context_manager.build_context_window(
            agent_id=agent_id,
            current_task=current_task,
            phase=current_phase,
            max_context_size=max_context_size,
            orchestrator=self.orchestrator,
        )

    def track_context_usage(
        self,
        agent_id: str,
        context: Any,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Track how agent used provided context.

        Args:
            agent_id: Agent identifier
            context: Context that was provided
            result: Result from agent execution

        Returns:
            Usage statistics
        """
        return self.context_manager.track_context_usage(agent_id, context, result)

    def evaluate_agent_performance(
        self,
        agent_id: str,
        cycle_id: str,
    ):
        """
        Evaluate agent performance for a completed cycle.

        Args:
            agent_id: Agent identifier
            cycle_id: ATO cycle ID

        Returns:
            AgentPerformanceMetrics
        """
        metrics = self.performance_evaluator.evaluate_agent_cycle_performance(
            agent_id=agent_id,
            cycle_id=cycle_id,
        )

        # Optimize context strategy based on performance
        adjustments = self.context_feedback.optimize_context_strategy(
            agent_id=agent_id,
            performance_metrics=metrics,
        )

        # Apply adjustments
        self.context_feedback.apply_adjustments(
            agent_id=agent_id,
            orchestrator=self.orchestrator,
        )

        return metrics

    def get_performance_report(self, agent_id: str, cycles: int = 5) -> str:
        """
        Get comprehensive performance report for an agent.

        Args:
            agent_id: Agent identifier
            cycles: Number of recent cycles to include

        Returns:
            Formatted report string
        """
        return self.performance_evaluator.generate_performance_report(
            agent_id=agent_id,
            cycles=cycles,
        )

    def get_context_optimization_report(self) -> str:
        """Get context strategy optimization report."""
        return self.context_feedback.generate_optimization_report()

    def get_context_performance_analysis(self) -> Dict[str, Any]:
        """Analyze correlation between context strategies and performance."""
        return self.context_feedback.analyze_context_performance_correlation()
