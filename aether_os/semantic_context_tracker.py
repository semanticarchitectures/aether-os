"""
Semantic Context Tracker for Aether OS.

Tracks context utilization using semantic similarity between
agent responses and provided context elements.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ContextElement:
    """Individual context element with metadata."""
    element_id: str
    content: str
    category: str  # doctrinal, situational, historical, collaborative
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    usage_count: int = 0
    last_used: Optional[datetime] = None


@dataclass
class ContextUsageRecord:
    """Record of context usage for a specific response."""
    response_text: str
    cited_elements: List[str]  # Explicitly cited element IDs
    semantically_similar_elements: List[Tuple[str, float]]  # (element_id, similarity_score)
    utilization_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CitationValidation:
    """Result of citation validation."""
    valid_citations: List[str]
    invalid_citations: List[str]
    missing_citations: List[str]  # Elements used but not cited
    citation_accuracy: float  # Percentage of valid citations


class SemanticContextTracker:
    """
    Tracks context utilization using semantic similarity.

    Features:
    - Embedding-based similarity measurement
    - Citation validation
    - Utilization scoring
    - Usage pattern analysis
    """

    def __init__(
        self,
        similarity_threshold: float = 0.5,
        use_embeddings: bool = True,
    ):
        """
        Initialize semantic context tracker.

        Args:
            similarity_threshold: Minimum similarity score to consider element "used"
            use_embeddings: Whether to use embeddings (requires sentence-transformers)
        """
        self.similarity_threshold = similarity_threshold
        self.use_embeddings = use_embeddings

        # Initialize embedding model if available
        self.embedding_model = None
        if use_embeddings:
            self._init_embedding_model()

        # Track context elements
        self.context_elements: Dict[str, ContextElement] = {}

        # Usage history
        self.usage_history: List[ContextUsageRecord] = []

        logger.info(
            f"SemanticContextTracker initialized "
            f"(embeddings={'enabled' if self.embedding_model else 'disabled'})"
        )

    def _init_embedding_model(self):
        """Initialize sentence embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        except ImportError:
            logger.warning(
                "sentence-transformers not available. "
                "Semantic tracking will use citation-based method only."
            )
            self.use_embeddings = False

    def register_context_elements(
        self,
        elements: List[ContextElement],
        compute_embeddings: bool = True,
    ):
        """
        Register context elements for tracking.

        Args:
            elements: List of context elements
            compute_embeddings: Whether to compute embeddings now
        """
        for element in elements:
            self.context_elements[element.element_id] = element

            # Compute embedding if requested
            if compute_embeddings and self.embedding_model and not element.embedding:
                element.embedding = self._compute_embedding(element.content)

        logger.info(f"Registered {len(elements)} context elements")

    def track_usage(
        self,
        response_text: str,
        cited_element_ids: List[str],
        all_element_ids: Optional[List[str]] = None,
    ) -> ContextUsageRecord:
        """
        Track context usage in a response.

        Args:
            response_text: Agent's response text
            cited_element_ids: Element IDs explicitly cited
            all_element_ids: All element IDs that were provided (for validation)

        Returns:
            ContextUsageRecord with usage details
        """
        # Find semantically similar elements if embeddings available
        similar_elements = []
        if self.embedding_model:
            similar_elements = self._find_similar_elements(response_text)

        # Calculate utilization score
        if all_element_ids:
            # Combine explicit citations and semantic similarity
            used_element_ids = set(cited_element_ids)
            used_element_ids.update([elem_id for elem_id, _ in similar_elements])

            utilization_score = len(used_element_ids) / len(all_element_ids)
        else:
            # Use citation count as proxy
            utilization_score = len(cited_element_ids) / max(len(self.context_elements), 1)

        # Update element usage counts
        for element_id in cited_element_ids:
            if element_id in self.context_elements:
                element = self.context_elements[element_id]
                element.usage_count += 1
                element.last_used = datetime.now()

        # Create usage record
        record = ContextUsageRecord(
            response_text=response_text,
            cited_elements=cited_element_ids,
            semantically_similar_elements=similar_elements,
            utilization_score=utilization_score,
            metadata={
                "total_elements_available": len(all_element_ids) if all_element_ids else len(self.context_elements),
                "embedding_based": self.embedding_model is not None,
            }
        )

        self.usage_history.append(record)

        logger.info(
            f"Tracked usage: {len(cited_element_ids)} citations, "
            f"{len(similar_elements)} semantic matches, "
            f"{utilization_score:.1%} utilization"
        )

        return record

    def validate_citations(
        self,
        cited_element_ids: List[str],
        response_text: str,
        all_element_ids: Optional[List[str]] = None,
    ) -> CitationValidation:
        """
        Validate citations against context elements.

        Args:
            cited_element_ids: Element IDs cited in response
            response_text: The response text
            all_element_ids: All available element IDs

        Returns:
            CitationValidation with validation results
        """
        valid_citations = []
        invalid_citations = []

        # Check each citation
        for element_id in cited_element_ids:
            if element_id in self.context_elements:
                valid_citations.append(element_id)
            else:
                invalid_citations.append(element_id)

        # Find missing citations (elements used but not cited)
        missing_citations = []
        if self.embedding_model and all_element_ids:
            # Find semantically similar elements
            similar_elements = self._find_similar_elements(response_text)

            for element_id, similarity in similar_elements:
                if element_id not in cited_element_ids and similarity > self.similarity_threshold:
                    missing_citations.append(element_id)

        # Calculate accuracy
        total_citations = len(cited_element_ids)
        citation_accuracy = len(valid_citations) / total_citations if total_citations > 0 else 1.0

        validation = CitationValidation(
            valid_citations=valid_citations,
            invalid_citations=invalid_citations,
            missing_citations=missing_citations,
            citation_accuracy=citation_accuracy,
        )

        if invalid_citations:
            logger.warning(f"Invalid citations found: {invalid_citations}")

        if missing_citations:
            logger.info(f"Missing citations (semantically used but not cited): {missing_citations}")

        return validation

    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text."""
        if not self.embedding_model:
            return None

        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}")
            return None

    def _find_similar_elements(
        self,
        response_text: str,
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Find context elements semantically similar to response.

        Args:
            response_text: Response to compare
            top_k: Number of top similar elements to return

        Returns:
            List of (element_id, similarity_score) tuples
        """
        if not self.embedding_model:
            return []

        # Compute response embedding
        response_embedding = self._compute_embedding(response_text)
        if response_embedding is None:
            return []

        # Compute similarities
        similarities = []
        for element_id, element in self.context_elements.items():
            if element.embedding is None:
                # Compute on-demand if missing
                element.embedding = self._compute_embedding(element.content)

            if element.embedding is not None:
                similarity = self._cosine_similarity(response_embedding, element.embedding)
                similarities.append((element_id, float(similarity)))

        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top-k above threshold
        return [
            (elem_id, score)
            for elem_id, score in similarities[:top_k]
            if score >= self.similarity_threshold
        ]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def get_utilization_stats(self) -> Dict[str, Any]:
        """Get overall utilization statistics."""
        if not self.usage_history:
            return {
                "total_interactions": 0,
                "average_utilization": 0.0,
                "total_elements": len(self.context_elements),
                "used_elements": 0,
            }

        # Calculate average utilization
        avg_utilization = np.mean([record.utilization_score for record in self.usage_history])

        # Count used elements
        used_elements = set()
        for record in self.usage_history:
            used_elements.update(record.cited_elements)

        # Find most and least used elements
        element_usage = [
            (elem_id, element.usage_count)
            for elem_id, element in self.context_elements.items()
        ]
        element_usage.sort(key=lambda x: x[1], reverse=True)

        stats = {
            "total_interactions": len(self.usage_history),
            "average_utilization": float(avg_utilization),
            "total_elements": len(self.context_elements),
            "used_elements": len(used_elements),
            "unused_elements": len(self.context_elements) - len(used_elements),
            "most_used": element_usage[:5] if element_usage else [],
            "least_used": element_usage[-5:] if element_usage else [],
        }

        return stats

    def get_element_usage(self, element_id: str) -> Dict[str, Any]:
        """Get usage statistics for a specific element."""
        if element_id not in self.context_elements:
            return {"error": f"Element {element_id} not found"}

        element = self.context_elements[element_id]

        return {
            "element_id": element_id,
            "category": element.category,
            "usage_count": element.usage_count,
            "last_used": element.last_used.isoformat() if element.last_used else None,
            "content_preview": element.content[:100] + "..." if len(element.content) > 100 else element.content,
        }

    def identify_underutilized_context(
        self,
        min_usage_threshold: int = 1,
    ) -> List[ContextElement]:
        """
        Identify context elements that are underutilized.

        Args:
            min_usage_threshold: Minimum usage count to not be considered underutilized

        Returns:
            List of underutilized context elements
        """
        underutilized = [
            element
            for element in self.context_elements.values()
            if element.usage_count < min_usage_threshold
        ]

        underutilized.sort(key=lambda x: x.usage_count)

        logger.info(f"Found {len(underutilized)} underutilized context elements")

        return underutilized

    def clear_history(self):
        """Clear usage history (keeps context elements)."""
        self.usage_history.clear()
        logger.info("Cleared usage history")

    def reset(self):
        """Reset tracker completely."""
        self.context_elements.clear()
        self.usage_history.clear()
        logger.info("Reset semantic context tracker")
