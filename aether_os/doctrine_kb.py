"""
Doctrine Knowledge Base for Aether OS.

Provides vector-based semantic search over USAF EMS doctrine documents
using ChromaDB for embeddings and retrieval.
"""

from typing import List, Dict, Optional, Any
import logging
import os
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed - doctrine KB will operate in limited mode")

logger = logging.getLogger(__name__)


class DoctrineKnowledgeBase:
    """
    Vector-based knowledge base for USAF EMS doctrine.

    Stores doctrine documents as embeddings for semantic search and retrieval.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize the doctrine knowledge base.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory or os.path.join(
            os.getcwd(), "doctrine_kb", "chroma_db"
        )

        if CHROMADB_AVAILABLE:
            self._initialize_chromadb()
        else:
            logger.warning("ChromaDB not available - using fallback mode")
            self.client = None
            self.collection = None

    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create persist directory if it doesn't exist
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="doctrine",
                metadata={"description": "USAF EMS doctrine documents"},
            )

            logger.info(
                f"DoctrineKnowledgeBase initialized "
                f"({self.collection.count()} documents loaded)"
            )

        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}", exc_info=True)
            self.client = None
            self.collection = None

    def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Query the doctrine knowledge base.

        Args:
            query: Natural language query
            filters: Optional metadata filters
            top_k: Number of results to return

        Returns:
            List of matching doctrine passages with metadata
        """
        if not self.collection:
            logger.warning("Doctrine KB not initialized - returning empty results")
            return []

        try:
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filters,
            )

            # Format results
            formatted_results = []
            if results and results['documents']:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None,
                    })

            logger.debug(f"Doctrine query returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error querying doctrine KB: {e}", exc_info=True)
            return []

    def get_procedure(self, procedure_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific doctrine procedure by name.

        Args:
            procedure_name: Name of the procedure

        Returns:
            Procedure document with metadata, or None if not found
        """
        if not self.collection:
            logger.warning("Doctrine KB not initialized")
            return None

        try:
            results = self.collection.query(
                query_texts=[procedure_name],
                n_results=1,
                where={"content_type": "procedure"},
            )

            if results and results['documents'] and len(results['documents'][0]) > 0:
                return {
                    "content": results['documents'][0][0],
                    "metadata": results['metadatas'][0][0] if results['metadatas'] else {},
                }

            logger.debug(f"Procedure '{procedure_name}' not found")
            return None

        except Exception as e:
            logger.error(f"Error retrieving procedure: {e}", exc_info=True)
            return None

    def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Add a document to the doctrine knowledge base.

        Args:
            document_id: Unique identifier for the document
            content: Document content
            metadata: Optional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.collection:
            logger.warning("Doctrine KB not initialized")
            return False

        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata or {}],
                ids=[document_id],
            )

            logger.info(f"Added document to doctrine KB: {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding document: {e}", exc_info=True)
            return False

    def add_documents_batch(
        self,
        documents: List[Dict[str, Any]],
    ) -> int:
        """
        Add multiple documents to the knowledge base.

        Args:
            documents: List of dicts with 'id', 'content', and 'metadata' keys

        Returns:
            Number of documents successfully added
        """
        if not self.collection:
            logger.warning("Doctrine KB not initialized")
            return 0

        try:
            ids = [doc['id'] for doc in documents]
            contents = [doc['content'] for doc in documents]
            metadatas = [doc.get('metadata', {}) for doc in documents]

            self.collection.add(
                documents=contents,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(f"Added {len(documents)} documents to doctrine KB")
            return len(documents)

        except Exception as e:
            logger.error(f"Error adding documents batch: {e}", exc_info=True)
            return 0

    def search_by_metadata(
        self,
        filters: Dict[str, Any],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for documents by metadata filters.

        Args:
            filters: Metadata filters (e.g., {"document": "AFI 10-703"})
            limit: Maximum number of results

        Returns:
            List of matching documents
        """
        if not self.collection:
            logger.warning("Doctrine KB not initialized")
            return []

        try:
            results = self.collection.get(
                where=filters,
                limit=limit,
            )

            formatted_results = []
            if results and results['documents']:
                for i in range(len(results['documents'])):
                    formatted_results.append({
                        "id": results['ids'][i],
                        "content": results['documents'][i],
                        "metadata": results['metadatas'][i] if results['metadatas'] else {},
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Error searching by metadata: {e}", exc_info=True)
            return []

    def count_documents(self) -> int:
        """Get total number of documents in the knowledge base."""
        if not self.collection:
            return 0
        return self.collection.count()

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the knowledge base.

        Args:
            document_id: ID of document to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.collection:
            logger.warning("Doctrine KB not initialized")
            return False

        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted document from doctrine KB: {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document: {e}", exc_info=True)
            return False
