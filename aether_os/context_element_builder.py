"""
Context Element Builder for Aether OS.

Converts AgentContext to ContextElements for semantic tracking.
"""

import logging
from typing import List, Dict, Any
from aether_os.agent_context import AgentContext
from aether_os.semantic_context_tracker import ContextElement

logger = logging.getLogger(__name__)


class ContextElementBuilder:
    """
    Builds ContextElements from AgentContext for semantic tracking.

    Assigns unique IDs to each context item and organizes them
    by category for tracking.
    """

    @staticmethod
    def build_elements(context: AgentContext) -> List[ContextElement]:
        """
        Build list of ContextElements from AgentContext.

        Args:
            context: AgentContext to convert

        Returns:
            List of ContextElements with unique IDs
        """
        elements = []

        # Process doctrinal context
        elements.extend(
            ContextElementBuilder._build_doctrinal_elements(context)
        )

        # Process situational context
        elements.extend(
            ContextElementBuilder._build_situational_elements(context)
        )

        # Process historical context
        elements.extend(
            ContextElementBuilder._build_historical_elements(context)
        )

        # Process collaborative context
        elements.extend(
            ContextElementBuilder._build_collaborative_elements(context)
        )

        logger.info(f"Built {len(elements)} context elements from AgentContext")

        return elements

    @staticmethod
    def _build_doctrinal_elements(context: AgentContext) -> List[ContextElement]:
        """Build doctrinal context elements."""
        elements = []

        # Procedures
        for idx, proc in enumerate(context.doctrinal_context.relevant_procedures):
            element_id = f"DOC-PROC-{idx:03d}"
            content = proc.get("content", str(proc)) if isinstance(proc, dict) else str(proc)

            elements.append(ContextElement(
                element_id=element_id,
                content=content,
                category="doctrinal",
                metadata={
                    "type": "procedure",
                    "source": proc.get("source", "unknown") if isinstance(proc, dict) else "unknown",
                }
            ))

        # Policies
        for idx, policy in enumerate(context.doctrinal_context.applicable_policies):
            element_id = f"DOC-POL-{idx:03d}"
            content = policy.get("content", str(policy)) if isinstance(policy, dict) else str(policy)

            elements.append(ContextElement(
                element_id=element_id,
                content=content,
                category="doctrinal",
                metadata={
                    "type": "policy",
                    "source": policy.get("source", "unknown") if isinstance(policy, dict) else "unknown",
                }
            ))

        # Best practices
        for idx, practice in enumerate(context.doctrinal_context.best_practices):
            element_id = f"DOC-BP-{idx:03d}"

            elements.append(ContextElement(
                element_id=element_id,
                content=practice,
                category="doctrinal",
                metadata={"type": "best_practice"}
            ))

        return elements

    @staticmethod
    def _build_situational_elements(context: AgentContext) -> List[ContextElement]:
        """Build situational context elements."""
        elements = []

        # Threats
        for threat in context.situational_context.current_threats:
            threat_id = threat.get("threat_id", f"THR-{len(elements):03d}")
            threat_type = threat.get("threat_type", "Unknown")
            location = threat.get("location", {})

            content = f"{threat_type} at ({location.get('lat', 'N/A')}, {location.get('lon', 'N/A')})"
            if "capability" in threat:
                content += f" - {threat['capability']}"
            if "priority" in threat:
                content += f" (Priority: {threat['priority']})"

            elements.append(ContextElement(
                element_id=threat_id,
                content=content,
                category="situational",
                metadata={
                    "type": "threat",
                    "full_data": threat,
                }
            ))

        # Assets
        for asset in context.situational_context.available_assets:
            asset_id = asset.get("asset_id", f"AST-{len(elements):03d}")
            platform = asset.get("platform", "Unknown")
            capability = asset.get("capability", "N/A")

            content = f"{platform} - {capability}"
            if "availability" in asset:
                content += f" (Status: {asset['availability']})"

            elements.append(ContextElement(
                element_id=asset_id,
                content=content,
                category="situational",
                metadata={
                    "type": "asset",
                    "full_data": asset,
                }
            ))

        # Missions
        for mission in context.situational_context.active_missions:
            mission_id = mission.get("mission_id", f"MSN-{len(elements):03d}")
            mission_type = mission.get("mission_type", "Unknown")

            content = f"{mission_type} mission"
            if "target" in mission:
                content += f" - Target: {mission['target']}"

            elements.append(ContextElement(
                element_id=mission_id,
                content=content,
                category="situational",
                metadata={
                    "type": "mission",
                    "full_data": mission,
                }
            ))

        # Spectrum status
        if context.situational_context.spectrum_status:
            element_id = "SPEC-STATUS"
            content = str(context.situational_context.spectrum_status)

            elements.append(ContextElement(
                element_id=element_id,
                content=content,
                category="situational",
                metadata={
                    "type": "spectrum",
                    "full_data": context.situational_context.spectrum_status,
                }
            ))

        return elements

    @staticmethod
    def _build_historical_elements(context: AgentContext) -> List[ContextElement]:
        """Build historical context elements."""
        elements = []

        # Lessons learned
        for idx, lesson in enumerate(context.historical_context.lessons_learned):
            element_id = f"HIST-LL-{idx:03d}"
            content = lesson.get("content", str(lesson)) if isinstance(lesson, dict) else str(lesson)

            elements.append(ContextElement(
                element_id=element_id,
                content=content,
                category="historical",
                metadata={
                    "type": "lesson_learned",
                    "full_data": lesson if isinstance(lesson, dict) else {"content": lesson},
                }
            ))

        # Performance patterns
        for idx, pattern in enumerate(context.historical_context.successful_patterns):
            element_id = f"HIST-PERF-{idx:03d}"
            content = pattern.get("description", str(pattern)) if isinstance(pattern, dict) else str(pattern)

            elements.append(ContextElement(
                element_id=element_id,
                content=content,
                category="historical",
                metadata={
                    "type": "performance_pattern",
                    "full_data": pattern if isinstance(pattern, dict) else {"description": pattern},
                }
            ))

        return elements

    @staticmethod
    def _build_collaborative_elements(context: AgentContext) -> List[ContextElement]:
        """Build collaborative context elements."""
        elements = []

        # Peer agent states
        for agent_id, state in context.collaborative_context.peer_agent_states.items():
            element_id = f"PEER-{agent_id}"
            content = f"{agent_id}: {state}"

            elements.append(ContextElement(
                element_id=element_id,
                content=content,
                category="collaborative",
                metadata={
                    "type": "peer_state",
                    "agent_id": agent_id,
                    "full_data": state,
                }
            ))

        # Shared artifacts
        for idx, artifact in enumerate(context.collaborative_context.shared_artifacts):
            element_id = f"ARTF-{idx:03d}"
            content = artifact.get("description", str(artifact)) if isinstance(artifact, dict) else str(artifact)

            elements.append(ContextElement(
                element_id=element_id,
                content=content,
                category="collaborative",
                metadata={
                    "type": "artifact",
                    "full_data": artifact if isinstance(artifact, dict) else {"description": artifact},
                }
            ))

        return elements

    @staticmethod
    def get_element_ids(elements: List[ContextElement]) -> List[str]:
        """Extract element IDs from list of elements."""
        return [elem.element_id for elem in elements]

    @staticmethod
    def get_elements_by_category(
        elements: List[ContextElement],
        category: str,
    ) -> List[ContextElement]:
        """Filter elements by category."""
        return [elem for elem in elements if elem.category == category]

    @staticmethod
    def merge_context_dict(
        original_dict: Dict[str, Any],
        element_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Merge element IDs back into context dictionary.

        Adds element_id fields to items in the context dict.
        """
        merged = original_dict.copy()

        # This would map element IDs back to their original items
        # For now, just add element_ids list
        merged["element_ids"] = element_ids

        return merged
