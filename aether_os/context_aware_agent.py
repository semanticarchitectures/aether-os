"""
Context-Aware Base Agent for Aether OS.

Base class for agents that use LLM-powered reasoning with
context-grounded decision making.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

from agents.base_agent import BaseAetherAgent
from aether_os.llm_client import LLMClient, LLMProvider
from aether_os.context_processor import ContextProcessor, ProcessedContext
from aether_os.prompt_builder import PromptBuilder
from aether_os.semantic_context_tracker import SemanticContextTracker, ContextElement
from aether_os.context_element_builder import ContextElementBuilder

logger = logging.getLogger(__name__)


class ContextAwareResponse(BaseModel):
    """Structured response from context-aware agent."""
    content: str
    context_citations: List[str] = []
    information_gaps: List[str] = []
    confidence: float = 0.8
    reasoning: Optional[str] = None


class ContextAwareBaseAgent(BaseAetherAgent):
    """
    Base class for context-aware agents with LLM integration.

    Extends BaseAetherAgent with:
    - LLM-powered reasoning
    - Context processing and injection
    - Semantic context tracking
    - Prompt template construction
    """

    def __init__(
        self,
        agent_id: str,
        aether_os: Any,
        role: str,
        llm_provider: LLMProvider = LLMProvider.ANTHROPIC,
        max_context_tokens: int = 8000,
        use_semantic_tracking: bool = True,
    ):
        """
        Initialize context-aware agent.

        Args:
            agent_id: Unique agent identifier
            aether_os: Aether OS instance
            role: Agent role (e.g., "ems_strategy", "ew_planner")
            llm_provider: Primary LLM provider
            max_context_tokens: Maximum tokens for context
            use_semantic_tracking: Enable semantic context tracking
        """
        super().__init__(agent_id=agent_id, aether_os=aether_os)

        self.role = role
        self.max_context_tokens = max_context_tokens

        # Initialize LLM client
        self.llm_client = LLMClient(primary_provider=llm_provider)

        # Initialize context processor
        self.context_processor = ContextProcessor()

        # Initialize prompt builder
        self.prompt_builder = PromptBuilder()

        # Initialize semantic context tracker
        self.semantic_tracker = None
        if use_semantic_tracking:
            self.semantic_tracker = SemanticContextTracker(
                similarity_threshold=0.5,
                use_embeddings=True,
            )
            logger.info(f"[{self.agent_id}] Semantic tracking enabled")

        # Track current context elements
        self.current_context_elements: List[ContextElement] = []

        # Track LLM availability
        self.llm_available = self.llm_client.is_available()

        if not self.llm_available:
            logger.warning(
                f"[{self.agent_id}] No LLM provider available. "
                "Agent will use fallback mode."
            )
        else:
            providers = self.llm_client.get_available_providers()
            logger.info(
                f"[{self.agent_id}] LLM providers available: {providers}"
            )

    def generate_with_context(
        self,
        task_description: str,
        output_schema: Optional[type] = None,
        additional_instructions: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> Dict[str, Any]:
        """
        Generate response using LLM with current context.

        Args:
            task_description: Task to perform
            output_schema: Pydantic model for structured output
            additional_instructions: Additional instructions
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Response dictionary with content and metadata
        """
        if not self.llm_available:
            return self._fallback_response(task_description)

        # Get current context
        context = self.current_context

        if not context:
            logger.warning(f"[{self.agent_id}] No context available")
            return self._fallback_response(task_description)

        # Build context elements for semantic tracking
        if self.semantic_tracker:
            self.current_context_elements = ContextElementBuilder.build_elements(context)
            self.semantic_tracker.register_context_elements(
                self.current_context_elements,
                compute_embeddings=True,
            )

        # Process context
        processed_context = self.context_processor.process(
            context=context,
            task_description=task_description,
            max_tokens=self.max_context_tokens,
        )

        # Build prompt
        system_prompt, user_prompt = self.prompt_builder.build_prompt(
            role=self.role,
            task_description=task_description,
            processed_context=processed_context,
            output_schema=output_schema.model_json_schema() if output_schema else None,
            additional_instructions=additional_instructions,
        )

        logger.info(
            f"[{self.agent_id}] Generating response with "
            f"{processed_context.total_tokens} tokens of context"
        )

        try:
            # Set agent ID for logging
            self.llm_client._current_agent_id = self.agent_id

            # Generate with LLM
            llm_response = self.llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                structured_output=output_schema,
            )

            # Extract citations from response
            citations = self.context_processor.extract_citations(llm_response.content)

            # Track usage with semantic tracker if available
            if self.semantic_tracker and self.current_context_elements:
                element_ids = ContextElementBuilder.get_element_ids(self.current_context_elements)

                # Track usage semantically
                usage_record = self.semantic_tracker.track_usage(
                    response_text=llm_response.content,
                    cited_element_ids=citations,
                    all_element_ids=element_ids,
                )

                # Validate citations
                citation_validation = self.semantic_tracker.validate_citations(
                    cited_element_ids=citations,
                    response_text=llm_response.content,
                    all_element_ids=element_ids,
                )

                utilization = usage_record.utilization_score
                citation_accuracy = citation_validation.citation_accuracy

                # Log validation results
                if citation_validation.invalid_citations:
                    logger.warning(
                        f"[{self.agent_id}] Invalid citations: {citation_validation.invalid_citations}"
                    )
                if citation_validation.missing_citations:
                    logger.info(
                        f"[{self.agent_id}] Missing citations (semantically used): "
                        f"{citation_validation.missing_citations[:3]}..."
                    )
            else:
                # Fallback: use simple citation-based utilization
                utilization = len(citations) / len(processed_context.element_ids) if processed_context.element_ids else 0.0
                citation_accuracy = 1.0

            # Track context usage (base implementation)
            if citations:
                self._track_context_usage(citations)

            logger.info(
                f"[{self.agent_id}] Generated response: "
                f"{llm_response.tokens_used} tokens, "
                f"{len(citations)} citations, "
                f"{utilization:.1%} utilization, "
                f"{citation_accuracy:.1%} citation accuracy"
            )

            result = {
                "success": True,
                "content": llm_response.content,
                "citations": citations,
                "context_utilization": utilization,
                "tokens_used": llm_response.tokens_used,
                "model": llm_response.model,
                "provider": llm_response.provider.value,
                "processed_context_tokens": processed_context.total_tokens,
                "context_truncated": processed_context.truncated,
            }

            # Add semantic tracking results if available
            if self.semantic_tracker:
                result["citation_accuracy"] = citation_accuracy
                result["semantic_tracking"] = True

            return result

        except Exception as e:
            logger.error(f"[{self.agent_id}] LLM generation failed: {e}", exc_info=True)
            return self._fallback_response(task_description, error=str(e))

    def _fallback_response(
        self,
        task_description: str,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate fallback response when LLM unavailable."""
        logger.info(f"[{self.agent_id}] Using fallback response")

        response = {
            "success": True,
            "content": f"Task acknowledged: {task_description}",
            "citations": [],
            "context_utilization": 0.0,
            "fallback_mode": True,
            "message": "LLM unavailable - using fallback mode",
        }

        if error:
            response["error"] = error

        return response

    def process_message_with_context(
        self,
        message_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process message using context-aware reasoning.

        Override this in subclasses to handle specific message types.

        Args:
            message_type: Type of message
            payload: Message payload

        Returns:
            Response dictionary
        """
        # Build task description from message
        task_description = f"Process {message_type} message: {payload}"

        # Generate response with context
        return self.generate_with_context(
            task_description=task_description,
        )

    def validate_against_doctrine(
        self,
        action: str,
        proposed_decision: str,
    ) -> Dict[str, Any]:
        """
        Validate a proposed decision against doctrine in context.

        Args:
            action: Action being considered
            proposed_decision: Proposed decision or plan

        Returns:
            Validation result with compliance assessment
        """
        task = f"""Validate the following proposed decision against provided doctrine:

ACTION: {action}

PROPOSED DECISION:
{proposed_decision}

Validation requirements:
1. Check if decision follows doctrinal procedures
2. Identify any doctrine violations
3. Cite specific doctrine elements that apply
4. Provide compliance score (0.0-1.0)
5. Recommend corrections if needed"""

        return self.generate_with_context(
            task_description=task,
            additional_instructions="Focus on doctrinal compliance. Be strict in evaluation.",
        )

    def identify_information_gaps(
        self,
        task: str,
        required_information: List[str],
    ) -> List[str]:
        """
        Identify what information is missing from context for a task.

        Args:
            task: Task to perform
            required_information: List of required information types

        Returns:
            List of missing information items
        """
        if not self.current_context:
            return required_information  # All missing

        # Check what's available in context
        gaps = []

        for req in required_information:
            # Simple check - could be enhanced with semantic search
            context_str = str(self.current_context).lower()
            if req.lower() not in context_str:
                gaps.append(req)

        if gaps:
            logger.info(f"[{self.agent_id}] Identified {len(gaps)} information gaps")

        return gaps

    def get_context_summary(self) -> str:
        """Get a brief summary of current context."""
        if not self.current_context:
            return "No context available"

        context = self.current_context

        parts = []

        # Doctrinal
        doc_count = len(context.doctrinal_context.get("procedures", []))
        if doc_count > 0:
            parts.append(f"{doc_count} doctrinal procedures")

        # Situational
        threats = len(context.situational_context.get("current_threats", []))
        assets = len(context.situational_context.get("available_assets", []))
        if threats > 0:
            parts.append(f"{threats} threats")
        if assets > 0:
            parts.append(f"{assets} assets")

        # Historical
        lessons = len(context.historical_context.get("lessons_learned", []))
        if lessons > 0:
            parts.append(f"{lessons} lessons learned")

        return ", ".join(parts) if parts else "Empty context"

    def _track_context_usage(self, citation_ids: List[str]):
        """
        Track which context elements were used.

        Args:
            citation_ids: List of context element IDs cited
        """
        # Track citations for this agent
        if hasattr(self, 'citation_history'):
            self.citation_history.extend(citation_ids)
        else:
            self.citation_history = citation_ids.copy()

        logger.debug(f"[{self.agent_id}] Tracked {len(citation_ids)} citations")

    def get_semantic_stats(self) -> Dict[str, Any]:
        """
        Get semantic context utilization statistics.

        Returns:
            Dictionary with utilization stats
        """
        if not self.semantic_tracker:
            return {"semantic_tracking": False}

        stats = self.semantic_tracker.get_utilization_stats()
        stats["semantic_tracking"] = True

        return stats

    def get_underutilized_context(self) -> List[ContextElement]:
        """
        Get context elements that are underutilized.

        Returns:
            List of underutilized context elements
        """
        if not self.semantic_tracker:
            return []

        return self.semantic_tracker.identify_underutilized_context(
            min_usage_threshold=1
        )
