"""
Agent Context Manager for Aether OS.

Manages context window building, refreshing, and optimization for agents.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

from aether_os.agent_context import (
    AgentContext,
    DoctrineContext,
    SituationalContext,
    HistoricalContext,
    CollaborativeContext,
    InformationItem,
    ContextRefreshTrigger,
)
from aether_os.orchestrator import ATOPhase
from aether_os.access_control import AGENT_PROFILES, InformationCategory
from aether_os.doctrine_kb import DoctrineKnowledgeBase
from aether_os.information_broker import AOCInformationBroker

logger = logging.getLogger(__name__)


# Phase-based context templates
PHASE_CONTEXT_TEMPLATES = {
    "PHASE1_OEG": {
        "ems_strategy_agent": {
            "doctrine_priority": ["strategy_development", "commander_guidance"],
            "threat_detail_level": "strategic",
            "asset_visibility": "aggregate",
            "historical_depth": 3,  # last N cycles
        }
    },
    "PHASE2_TARGET_DEVELOPMENT": {
        "ems_strategy_agent": {
            "doctrine_priority": ["target_development", "ems_requirements"],
            "threat_detail_level": "operational",
            "asset_visibility": "aggregate",
            "historical_depth": 2,
        }
    },
    "PHASE3_WEAPONEERING": {
        "ew_planner_agent": {
            "doctrine_priority": ["mission_planning", "asset_assignment"],
            "threat_detail_level": "tactical",
            "asset_visibility": "detailed",
            "historical_depth": 1,
        },
        "spectrum_manager_agent": {
            "doctrine_priority": ["jceoi_process", "deconfliction"],
            "threat_detail_level": "frequency_bands",
            "asset_visibility": "spectrum_capable_only",
            "historical_depth": 1,
        }
    },
    "PHASE4_ATO_PRODUCTION": {
        "ato_producer_agent": {
            "doctrine_priority": ["ato_integration", "mission_approval"],
            "threat_detail_level": "summary",
            "asset_visibility": "assigned",
            "historical_depth": 1,
        }
    },
    "PHASE5_EXECUTION": {
        "spectrum_manager_agent": {
            "doctrine_priority": ["emergency_procedures", "conflict_resolution"],
            "threat_detail_level": "real_time",
            "asset_visibility": "active",
            "historical_depth": 0,
        }
    },
    "PHASE6_ASSESSMENT": {
        "assessment_agent": {
            "doctrine_priority": ["assessment", "lessons_learned"],
            "threat_detail_level": "summary",
            "asset_visibility": "summary",
            "historical_depth": 5,
        }
    },
}


class AgentContextManager:
    """
    Manages context provisioning for agents.

    Responsibilities:
    - Build role-appropriate context windows
    - Refresh context on phase transitions and triggers
    - Prioritize information by relevance
    - Enforce context size limits
    - Track context effectiveness
    """

    def __init__(
        self,
        doctrine_kb: DoctrineKnowledgeBase,
        information_broker: AOCInformationBroker,
    ):
        """
        Initialize context manager.

        Args:
            doctrine_kb: Doctrine knowledge base
            information_broker: Information broker for data access
        """
        self.doctrine_kb = doctrine_kb
        self.information_broker = information_broker

        # Track contexts for all agents
        self.agent_contexts: Dict[str, AgentContext] = {}

        # Context usage tracking
        self.context_usage_log: List[Dict[str, Any]] = []

        logger.info("AgentContextManager initialized")

    def build_context_window(
        self,
        agent_id: str,
        current_task: str,
        phase: ATOPhase,
        max_context_size: int = 32000,  # tokens
        orchestrator: Any = None,
    ) -> AgentContext:
        """
        Build optimized context window for agent's current task.

        Args:
            agent_id: Agent identifier
            current_task: Current task being performed
            phase: Current ATO phase
            max_context_size: Maximum context size in tokens
            orchestrator: ATO cycle orchestrator (for accessing cycle data)

        Returns:
            AgentContext with all relevant information
        """
        logger.info(
            f"Building context window for {agent_id} in {phase.value if phase else 'N/A'} "
            f"(max size: {max_context_size} tokens)"
        )

        # Create context
        context = AgentContext(
            agent_id=agent_id,
            current_phase=phase,
            current_task=current_task,
        )

        # Get context template for this agent/phase
        template = self._get_context_template(agent_id, phase)

        # Build doctrine context
        context.doctrinal_context = self._build_doctrine_context(
            agent_id, current_task, template
        )

        # Build situational context
        context.situational_context = self._build_situational_context(
            agent_id, phase, template, orchestrator
        )

        # Build historical context
        context.historical_context = self._build_historical_context(
            agent_id, template
        )

        # Build collaborative context
        context.collaborative_context = self._build_collaborative_context(
            agent_id, orchestrator
        )

        # Check size and prune if necessary
        if context.total_size() > max_context_size:
            context = self._prune_context_by_relevance(context, max_context_size)

        # Store context
        self.agent_contexts[agent_id] = context

        logger.info(
            f"Built context for {agent_id}: {context.total_size()} tokens "
            f"(doctrine: {context.doctrinal_context.size()}, "
            f"situational: {context.situational_context.size()}, "
            f"historical: {context.historical_context.size()}, "
            f"collaborative: {context.collaborative_context.size()})"
        )

        return context

    def _get_context_template(
        self,
        agent_id: str,
        phase: ATOPhase,
    ) -> Dict[str, Any]:
        """Get context template for agent in current phase."""
        if not phase:
            # Default template
            return {
                "doctrine_priority": ["general"],
                "threat_detail_level": "summary",
                "asset_visibility": "summary",
                "historical_depth": 1,
            }

        phase_templates = PHASE_CONTEXT_TEMPLATES.get(phase.value, {})
        return phase_templates.get(agent_id, {})

    def _build_doctrine_context(
        self,
        agent_id: str,
        current_task: str,
        template: Dict[str, Any],
    ) -> DoctrineContext:
        """Build doctrinal context for agent."""
        context = DoctrineContext()

        # Get doctrine priorities from template
        priorities = template.get("doctrine_priority", ["general"])

        # Query doctrine for each priority
        for priority in priorities:
            query = f"{priority} for {agent_id} {current_task}"
            results = self.doctrine_kb.query(query, top_k=3)

            for result in results:
                context.relevant_procedures.append({
                    "procedure_id": result.get("metadata", {}).get("document", "unknown"),
                    "relevance_score": 1.0 - (result.get("distance", 0.5)),
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                })

        # Add general best practices
        agent_profile = AGENT_PROFILES.get(agent_id)
        if agent_profile:
            role = agent_profile.role
            context.best_practices = self._get_best_practices(role)

        return context

    def _build_situational_context(
        self,
        agent_id: str,
        phase: ATOPhase,
        template: Dict[str, Any],
        orchestrator: Any,
    ) -> SituationalContext:
        """Build situational context for agent."""
        context = SituationalContext()

        agent_profile = AGENT_PROFILES.get(agent_id)
        if not agent_profile:
            return context

        # Get threat data if authorized
        if InformationCategory.THREAT_DATA in agent_profile.authorized_categories:
            threat_result = self.information_broker.query(
                agent_profile=agent_profile,
                category=InformationCategory.THREAT_DATA,
                query_params={"query": "all_threats"},
                current_phase=phase.value if phase else None,
            )
            if threat_result.get("success"):
                context.current_threats = threat_result.get("data", [])

        # Get asset data if authorized
        if InformationCategory.ASSET_STATUS in agent_profile.authorized_categories:
            asset_result = self.information_broker.query(
                agent_profile=agent_profile,
                category=InformationCategory.ASSET_STATUS,
                query_params={"asset_types": None},
                current_phase=phase.value if phase else None,
            )
            if asset_result.get("success"):
                context.available_assets = asset_result.get("data", [])

        # Get current cycle data if available
        if orchestrator and orchestrator.current_cycle:
            cycle = orchestrator.current_cycle
            context.active_missions = cycle.outputs.get("ew_missions", [])
            context.spectrum_status = {
                "allocations": cycle.outputs.get("frequency_allocations", []),
                "phase": phase.value if phase else None,
            }

        return context

    def _build_historical_context(
        self,
        agent_id: str,
        template: Dict[str, Any],
    ) -> HistoricalContext:
        """Build historical context from past cycles."""
        context = HistoricalContext()

        depth = template.get("historical_depth", 1)

        # Add lessons learned (would query from database in production)
        context.lessons_learned = [
            "Coordinate spectrum early to avoid conflicts",
            "Validate all mission approvals before ATO publication",
            "Monitor for EA/SIGINT fratricide during planning",
        ][:depth]

        return context

    def _build_collaborative_context(
        self,
        agent_id: str,
        orchestrator: Any,
    ) -> CollaborativeContext:
        """Build collaborative context about other agents."""
        context = CollaborativeContext()

        # Get current cycle outputs (shared artifacts)
        if orchestrator and orchestrator.current_cycle:
            cycle = orchestrator.current_cycle

            for output_name, output_data in cycle.outputs.items():
                context.shared_artifacts.append({
                    "artifact_name": output_name,
                    "artifact_type": "cycle_output",
                    "data": output_data,
                })

        return context

    def _get_best_practices(self, role: str) -> List[str]:
        """Get best practices for a role."""
        practices = {
            "ems_strategy": [
                "Align EMS strategy with overall air component strategy",
                "Consider full spectrum: EA, EP, ES operations",
                "Coordinate with intelligence community",
            ],
            "spectrum_manager": [
                "Follow JCEOI process for all allocations",
                "Coordinate with all spectrum users",
                "Maintain emergency reallocation procedures",
            ],
            "ew_planner": [
                "Check for EA/SIGINT fratricide",
                "Integrate EW with kinetic operations",
                "Request spectrum early",
            ],
            "ato_producer": [
                "Validate all mission approvals",
                "Integrate EMS with strike packages",
                "Generate complete SPINS annex",
            ],
            "assessment": [
                "Assess both effectiveness and process",
                "Identify improvement opportunities",
                "Generate actionable lessons learned",
            ],
        }

        return practices.get(role, [])

    def _prune_context_by_relevance(
        self,
        context: AgentContext,
        max_size: int,
    ) -> AgentContext:
        """
        Prune context to fit within token budget.

        Strategy:
        1. Always retain high-priority doctrine
        2. Reduce historical context first
        3. Summarize situational context if needed
        4. Maintain minimum collaborative context
        """
        current_size = context.total_size()

        if current_size <= max_size:
            return context

        logger.warning(
            f"Context size ({current_size}) exceeds max ({max_size}), pruning..."
        )

        # Calculate reduction needed
        reduction_needed = current_size - max_size

        # Prune historical context first (30% reduction)
        if context.historical_context.size() > 0:
            reduction = min(
                reduction_needed,
                int(context.historical_context.size() * 0.3)
            )
            context.historical_context.lessons_learned = (
                context.historical_context.lessons_learned[:2]
            )

        # Prune situational context if still needed (20% reduction)
        if context.total_size() > max_size:
            # Limit threats to top 5
            context.situational_context.current_threats = (
                context.situational_context.current_threats[:5]
            )
            # Limit assets to top 10
            context.situational_context.available_assets = (
                context.situational_context.available_assets[:10]
            )

        logger.info(f"Context pruned to {context.total_size()} tokens")

        return context

    def refresh_context(
        self,
        agent_id: str,
        trigger: ContextRefreshTrigger,
        orchestrator: Any = None,
    ) -> AgentContext:
        """
        Refresh context based on trigger.

        Args:
            agent_id: Agent identifier
            trigger: What triggered the refresh
            orchestrator: ATO cycle orchestrator

        Returns:
            Updated AgentContext
        """
        logger.info(f"Refreshing context for {agent_id} (trigger: {trigger.value})")

        # Get existing context or build new one
        existing = self.agent_contexts.get(agent_id)

        if not existing:
            logger.warning(f"No existing context for {agent_id}, building new one")
            return self.build_context_window(
                agent_id=agent_id,
                current_task="unknown",
                phase=orchestrator.get_current_phase() if orchestrator else None,
                orchestrator=orchestrator,
            )

        # Rebuild context with current phase
        refreshed = self.build_context_window(
            agent_id=agent_id,
            current_task=existing.current_task or "unknown",
            phase=orchestrator.get_current_phase() if orchestrator else existing.current_phase,
            orchestrator=orchestrator,
        )

        refreshed.last_refresh = datetime.now()

        return refreshed

    def track_context_usage(
        self,
        agent_id: str,
        context: AgentContext,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Track how agent used the provided context.

        Args:
            agent_id: Agent identifier
            context: Context that was provided
            result: Result from agent execution

        Returns:
            Usage statistics
        """
        utilization = context.get_utilization_rate()

        usage_log = {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "context_size": context.total_size(),
            "items_provided": (
                len(context.doctrinal_context.relevant_procedures) +
                len(context.situational_context.current_threats) +
                len(context.situational_context.available_assets)
            ),
            "items_referenced": len(context.items_referenced),
            "utilization_rate": utilization,
        }

        self.context_usage_log.append(usage_log)

        logger.debug(
            f"Context usage: {agent_id} used {utilization:.1%} of provided context"
        )

        return usage_log

    def get_context_statistics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get context usage statistics."""
        logs = self.context_usage_log

        if agent_id:
            logs = [log for log in logs if log["agent_id"] == agent_id]

        if not logs:
            return {}

        avg_utilization = sum(log["utilization_rate"] for log in logs) / len(logs)
        avg_size = sum(log["context_size"] for log in logs) / len(logs)

        return {
            "total_contexts_provided": len(logs),
            "avg_utilization_rate": avg_utilization,
            "avg_context_size": avg_size,
            "logs": logs,
        }
