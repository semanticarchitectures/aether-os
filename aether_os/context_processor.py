"""
Context Processor for Aether OS.

Processes agent context for LLM consumption with relevance scoring,
prioritization, and token budget management.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import tiktoken

from aether_os.agent_context import AgentContext

logger = logging.getLogger(__name__)


@dataclass
class ProcessedContext:
    """Processed context ready for LLM consumption."""
    doctrinal_context: str
    situational_context: str
    historical_context: str
    collaborative_context: str
    total_tokens: int
    element_ids: List[str]  # IDs of included context elements
    truncated: bool = False


class ContextProcessor:
    """
    Processes agent context for LLM consumption.

    Features:
    - Relevance scoring based on task
    - Priority-based filtering
    - Token budget management
    - Context formatting for prompts
    """

    def __init__(self, encoding_model: str = "cl100k_base"):
        """
        Initialize context processor.

        Args:
            encoding_model: Tiktoken encoding model for token counting
        """
        try:
            self.encoding = tiktoken.get_encoding(encoding_model)
        except Exception as e:
            logger.warning(f"Could not load tiktoken encoding: {e}. Using fallback.")
            self.encoding = None

    def process(
        self,
        context: AgentContext,
        task_description: Optional[str] = None,
        max_tokens: int = 8000,
        prioritize_recent: bool = True,
    ) -> ProcessedContext:
        """
        Process agent context for LLM consumption.

        Args:
            context: Agent context to process
            task_description: Task description for relevance scoring
            max_tokens: Maximum tokens to include
            prioritize_recent: Prioritize recent items in historical context

        Returns:
            ProcessedContext ready for LLM
        """
        logger.info(f"Processing context (max tokens: {max_tokens})")

        element_ids = []
        truncated = False

        # Process doctrinal context
        doctrinal_text, doc_ids = self._format_doctrinal_context(
            context.doctrinal_context,
            task_description,
        )

        # Process situational context
        situational_text, sit_ids = self._format_situational_context(
            context.situational_context
        )

        # Process historical context
        historical_text, hist_ids = self._format_historical_context(
            context.historical_context,
            prioritize_recent,
        )

        # Process collaborative context
        collaborative_text, collab_ids = self._format_collaborative_context(
            context.collaborative_context
        )

        # Combine and check token budget
        all_sections = [
            ("doctrinal", doctrinal_text, doc_ids, 0.4),  # 40% of budget
            ("situational", situational_text, sit_ids, 0.3),  # 30% of budget
            ("historical", historical_text, hist_ids, 0.2),  # 20% of budget
            ("collaborative", collaborative_text, collab_ids, 0.1),  # 10% of budget
        ]

        # Fit within token budget
        final_sections, final_ids, total_tokens, truncated = self._fit_token_budget(
            all_sections, max_tokens
        )

        processed = ProcessedContext(
            doctrinal_context=final_sections.get("doctrinal", ""),
            situational_context=final_sections.get("situational", ""),
            historical_context=final_sections.get("historical", ""),
            collaborative_context=final_sections.get("collaborative", ""),
            total_tokens=total_tokens,
            element_ids=final_ids,
            truncated=truncated,
        )

        logger.info(
            f"Processed context: {total_tokens} tokens, "
            f"{len(final_ids)} elements, truncated={truncated}"
        )

        return processed

    def _format_doctrinal_context(
        self,
        doctrinal_context: Dict[str, Any],
        task_description: Optional[str],
    ) -> Tuple[str, List[str]]:
        """Format doctrinal context section."""
        procedures = doctrinal_context.get("procedures", [])
        policies = doctrinal_context.get("policies", [])
        best_practices = doctrinal_context.get("best_practices", [])

        sections = []
        element_ids = []

        if procedures:
            sections.append("DOCTRINAL PROCEDURES:")
            for idx, proc in enumerate(procedures):
                element_id = f"DOC-PROC-{idx:03d}"
                element_ids.append(element_id)
                sections.append(f"[{element_id}] {proc}")

        if policies:
            sections.append("\nDOCTRINAL POLICIES:")
            for idx, policy in enumerate(policies):
                element_id = f"DOC-POL-{idx:03d}"
                element_ids.append(element_id)
                sections.append(f"[{element_id}] {policy}")

        if best_practices:
            sections.append("\nBEST PRACTICES:")
            for idx, practice in enumerate(best_practices):
                element_id = f"DOC-BP-{idx:03d}"
                element_ids.append(element_id)
                sections.append(f"[{element_id}] {practice}")

        return "\n".join(sections), element_ids

    def _format_situational_context(
        self,
        situational_context: Dict[str, Any],
    ) -> Tuple[str, List[str]]:
        """Format situational context section."""
        threats = situational_context.get("current_threats", [])
        assets = situational_context.get("available_assets", [])
        missions = situational_context.get("active_missions", [])
        spectrum = situational_context.get("spectrum_status", {})

        sections = []
        element_ids = []

        if threats:
            sections.append("CURRENT THREATS:")
            for threat in threats:
                threat_id = threat.get("threat_id", f"THR-{len(element_ids):03d}")
                element_ids.append(threat_id)
                threat_type = threat.get("threat_type", "Unknown")
                location = threat.get("location", {})
                sections.append(
                    f"[{threat_id}] {threat_type} at "
                    f"({location.get('lat', 'N/A')}, {location.get('lon', 'N/A')})"
                )
                if "capability" in threat:
                    sections.append(f"  Capability: {threat['capability']}")
                if "priority" in threat:
                    sections.append(f"  Priority: {threat['priority']}")

        if assets:
            sections.append("\nAVAILABLE ASSETS:")
            for asset in assets:
                asset_id = asset.get("asset_id", f"AST-{len(element_ids):03d}")
                element_ids.append(asset_id)
                platform = asset.get("platform", "Unknown")
                capability = asset.get("capability", "N/A")
                sections.append(f"[{asset_id}] {platform} - {capability}")
                if "availability" in asset:
                    sections.append(f"  Status: {asset['availability']}")

        if missions:
            sections.append("\nACTIVE MISSIONS:")
            for mission in missions:
                mission_id = mission.get("mission_id", f"MSN-{len(element_ids):03d}")
                element_ids.append(mission_id)
                mission_type = mission.get("mission_type", "Unknown")
                sections.append(f"[{mission_id}] {mission_type}")

        if spectrum:
            sections.append("\nSPECTRUM STATUS:")
            element_id = "SPEC-STATUS"
            element_ids.append(element_id)
            sections.append(f"[{element_id}] {spectrum}")

        return "\n".join(sections), element_ids

    def _format_historical_context(
        self,
        historical_context: Dict[str, Any],
        prioritize_recent: bool,
    ) -> Tuple[str, List[str]]:
        """Format historical context section."""
        lessons_learned = historical_context.get("lessons_learned", [])
        performance_patterns = historical_context.get("performance_patterns", [])

        sections = []
        element_ids = []

        if lessons_learned:
            sections.append("LESSONS LEARNED:")
            # Reverse if prioritizing recent
            items = reversed(lessons_learned) if prioritize_recent else lessons_learned
            for idx, lesson in enumerate(items):
                element_id = f"HIST-LL-{idx:03d}"
                element_ids.append(element_id)
                if isinstance(lesson, dict):
                    sections.append(f"[{element_id}] {lesson.get('content', str(lesson))}")
                else:
                    sections.append(f"[{element_id}] {lesson}")

        if performance_patterns:
            sections.append("\nPERFORMANCE PATTERNS:")
            for idx, pattern in enumerate(performance_patterns):
                element_id = f"HIST-PERF-{idx:03d}"
                element_ids.append(element_id)
                sections.append(f"[{element_id}] {pattern}")

        return "\n".join(sections), element_ids

    def _format_collaborative_context(
        self,
        collaborative_context: Dict[str, Any],
    ) -> Tuple[str, List[str]]:
        """Format collaborative context section."""
        peer_states = collaborative_context.get("peer_agent_states", {})
        shared_artifacts = collaborative_context.get("shared_artifacts", [])

        sections = []
        element_ids = []

        if peer_states:
            sections.append("PEER AGENT STATES:")
            for agent_id, state in peer_states.items():
                element_id = f"PEER-{agent_id}"
                element_ids.append(element_id)
                sections.append(f"[{element_id}] {agent_id}: {state}")

        if shared_artifacts:
            sections.append("\nSHARED ARTIFACTS:")
            for idx, artifact in enumerate(shared_artifacts):
                element_id = f"ARTF-{idx:03d}"
                element_ids.append(element_id)
                sections.append(f"[{element_id}] {artifact}")

        return "\n".join(sections), element_ids

    def _fit_token_budget(
        self,
        sections: List[Tuple[str, str, List[str], float]],
        max_tokens: int,
    ) -> Tuple[Dict[str, str], List[str], int, bool]:
        """
        Fit sections within token budget.

        Args:
            sections: List of (name, text, ids, weight) tuples
            max_tokens: Maximum total tokens

        Returns:
            (final_sections, element_ids, total_tokens, truncated)
        """
        final_sections = {}
        all_ids = []
        total_tokens = 0
        truncated = False

        # Allocate tokens proportionally
        for name, text, ids, weight in sections:
            if not text:
                continue

            section_budget = int(max_tokens * weight)
            section_tokens = self._count_tokens(text)

            if section_tokens <= section_budget:
                # Fits within budget
                final_sections[name] = text
                all_ids.extend(ids)
                total_tokens += section_tokens
            else:
                # Truncate to fit
                truncated_text = self._truncate_to_tokens(text, section_budget)
                final_sections[name] = truncated_text + "\n[... truncated ...]"
                # Keep proportional IDs
                keep_ratio = section_budget / section_tokens
                keep_count = max(1, int(len(ids) * keep_ratio))
                all_ids.extend(ids[:keep_count])
                total_tokens += section_budget
                truncated = True

        return final_sections, all_ids, total_tokens, truncated

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token budget."""
        if self.encoding:
            tokens = self.encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text
            truncated_tokens = tokens[:max_tokens]
            return self.encoding.decode(truncated_tokens)
        else:
            # Fallback: truncate by characters
            max_chars = max_tokens * 4
            return text[:max_chars]

    def extract_citations(self, response_text: str) -> List[str]:
        """
        Extract context element IDs cited in response.

        Looks for patterns like [DOC-001], [THR-001], etc.

        Args:
            response_text: Agent response text

        Returns:
            List of cited element IDs
        """
        import re
        pattern = r'\[([A-Z]+-[A-Z0-9-]+)\]'
        matches = re.findall(pattern, response_text)
        return list(set(matches))  # Unique citations
