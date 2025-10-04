#!/usr/bin/env python3
"""
PDF Document Integration Example for Aether OS

This script demonstrates how to:
1. Process PDF documents and extract text
2. Chunk documents into manageable sections
3. Add documents to the doctrine knowledge base
4. Show how agents access the content through context

Usage:
    python examples/pdf_document_integration.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aether_os.doctrine_kb import DoctrineKnowledgeBase
from aether_os.context_manager import AgentContextManager
from aether_os.information_broker import AOCInformationBroker
from aether_os.access_control import AGENT_PROFILES
from aether_os.orchestrator import ATOPhase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Note: This is a placeholder implementation. In production, you would use
    libraries like PyPDF2, pdfplumber, or pymupdf for actual PDF processing.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    # Placeholder - in reality you'd use a PDF library
    logger.info(f"Extracting text from PDF: {pdf_path}")
    
    # Simulate PDF content extraction
    return """
    USAF EMS Operations Manual
    
    Chapter 1: Strategic EMS Planning
    
    1.1 Overview
    Electronic Warfare (EW) operations are critical components of modern air operations.
    The electromagnetic spectrum (EMS) provides opportunities for both offensive and
    defensive operations that can significantly impact mission success.
    
    1.2 Planning Considerations
    EMS planning must be integrated with overall mission planning from the earliest
    stages. Key considerations include:
    - Threat emitter analysis
    - Friendly spectrum requirements
    - Deconfliction procedures
    - Mission timing and coordination
    
    Chapter 2: Frequency Management
    
    2.1 JCEOI Process
    The Joint Communications-Electronics Operating Instructions (JCEOI) process
    governs all frequency allocations in joint operations. This process ensures
    deconfliction between all spectrum users.
    
    2.2 Allocation Procedures
    Frequency allocation requests must be submitted through proper channels
    with sufficient lead time for coordination. Emergency allocations may be
    granted during active operations under specific circumstances.
    
    Chapter 3: Mission Execution
    
    3.1 Real-time Management
    During mission execution, spectrum managers must monitor for conflicts
    and be prepared to implement emergency reallocation procedures.
    
    3.2 Emergency Procedures
    When spectrum conflicts arise during operations, the spectrum manager
    has authority to implement emergency reallocations to maintain mission
    effectiveness while minimizing interference.
    """


def chunk_document_by_sections(text: str, document_name: str) -> List[Dict[str, Any]]:
    """
    Chunk a document into logical sections for the knowledge base.
    
    Args:
        text: Full document text
        document_name: Name of the source document
        
    Returns:
        List of document chunks with metadata
    """
    logger.info(f"Chunking document: {document_name}")
    
    # Simple chunking by chapters/sections
    # In production, you'd use more sophisticated chunking strategies
    chunks = []
    
    # Split by chapters
    sections = text.split("Chapter")
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        # Extract chapter info
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Get chapter title
        chapter_title = lines[0].strip() if lines else f"Section {i}"
        
        # Create chunk
        chunk = {
            'id': f"{document_name.replace(' ', '-').upper()}-CHAPTER-{i}",
            'content': f"Chapter {section.strip()}",
            'metadata': {
                'document': document_name,
                'section': chapter_title,
                'source_type': 'pdf',
                'authority_level': 'Service',
                'content_type': 'doctrine',
                'applicable_roles': 'ew_planner,spectrum_manager,ems_strategy',
                'chapter_number': str(i)
            }
        }
        chunks.append(chunk)
    
    logger.info(f"Created {len(chunks)} chunks from document")
    return chunks


def add_pdf_to_doctrine_kb(pdf_path: str, document_name: str, doctrine_kb: DoctrineKnowledgeBase) -> int:
    """
    Process a PDF and add it to the doctrine knowledge base.
    
    Args:
        pdf_path: Path to the PDF file
        document_name: Name to use for the document
        doctrine_kb: Doctrine knowledge base instance
        
    Returns:
        Number of chunks successfully added
    """
    logger.info(f"Processing PDF: {pdf_path}")
    
    # Extract text from PDF
    text_content = extract_pdf_text(pdf_path)
    
    # Chunk the document
    chunks = chunk_document_by_sections(text_content, document_name)
    
    # Add chunks to knowledge base
    added_count = 0
    for chunk in chunks:
        success = doctrine_kb.add_document(
            document_id=chunk['id'],
            content=chunk['content'],
            metadata=chunk['metadata']
        )
        if success:
            added_count += 1
    
    logger.info(f"Successfully added {added_count}/{len(chunks)} chunks to doctrine KB")
    return added_count


def demonstrate_agent_access(doctrine_kb: DoctrineKnowledgeBase):
    """
    Demonstrate how different agents access the PDF content.
    
    Args:
        doctrine_kb: Doctrine knowledge base with PDF content
    """
    logger.info("Demonstrating agent access to PDF content...")
    
    # Initialize context management
    info_broker = AOCInformationBroker(doctrine_kb=doctrine_kb)
    context_manager = AgentContextManager(doctrine_kb=doctrine_kb, information_broker=info_broker)
    
    # Test scenarios for different agents
    test_scenarios = [
        {
            'agent_id': 'ew_planner_agent',
            'task': 'Plan EW missions against air defense threats',
            'phase': ATOPhase.PHASE3_WEAPONEERING
        },
        {
            'agent_id': 'spectrum_manager_agent', 
            'task': 'Allocate frequencies for EW operations',
            'phase': ATOPhase.PHASE3_WEAPONEERING
        },
        {
            'agent_id': 'ems_strategy_agent',
            'task': 'Develop comprehensive EMS strategy',
            'phase': ATOPhase.PHASE1_OEG
        }
    ]
    
    print("\n" + "="*60)
    print("AGENT CONTEXT ACCESS DEMONSTRATION")
    print("="*60)
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['agent_id'].upper()} ---")
        print(f"Task: {scenario['task']}")
        print(f"Phase: {scenario['phase'].value}")
        
        # Build context for this agent
        context = context_manager.build_context_window(
            agent_id=scenario['agent_id'],
            current_task=scenario['task'],
            phase=scenario['phase'],
            max_context_size=32000
        )
        
        print(f"Context size: {context.total_size()} tokens")
        print(f"Doctrine procedures: {len(context.doctrinal_context.relevant_procedures)}")
        
        # Show the most relevant content
        procedures = context.doctrinal_context.relevant_procedures
        if procedures:
            print("Most relevant content:")
            for i, proc in enumerate(procedures[:2]):  # Show top 2
                doc_name = proc.get('metadata', {}).get('document', 'Unknown')
                section = proc.get('metadata', {}).get('section', 'Unknown')
                relevance = proc.get('relevance_score', 0)
                
                print(f"  {i+1}. {doc_name} - {section}")
                print(f"     Relevance: {relevance:.2f}")
                
                # Show content preview
                content = proc.get('content', '')
                preview = content[:150].replace('\n', ' ').strip() + '...'
                print(f"     Preview: {preview}")
        else:
            print("No relevant doctrine content found")


def query_doctrine_directly(doctrine_kb: DoctrineKnowledgeBase):
    """
    Demonstrate direct queries to the doctrine knowledge base.
    
    Args:
        doctrine_kb: Doctrine knowledge base instance
    """
    print("\n" + "="*60)
    print("DIRECT DOCTRINE QUERIES")
    print("="*60)
    
    # Test queries that agents might make
    test_queries = [
        "frequency allocation procedures",
        "EW mission planning considerations", 
        "emergency reallocation authority",
        "JCEOI process requirements",
        "spectrum deconfliction procedures"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = doctrine_kb.query(query, top_k=2)
        
        if results:
            for i, result in enumerate(results):
                doc = result.get('metadata', {}).get('document', 'Unknown')
                section = result.get('metadata', {}).get('section', 'Unknown')
                distance = result.get('distance', 1.0)
                relevance = 1.0 - distance
                
                print(f"  {i+1}. {doc} - {section} (relevance: {relevance:.2f})")
        else:
            print("  No results found")


def main():
    """Main demonstration function."""
    print("PDF Document Integration Demo for Aether OS")
    print("=" * 50)
    
    # Initialize doctrine knowledge base
    print("\n1. Initializing Doctrine Knowledge Base...")
    doctrine_kb = DoctrineKnowledgeBase()
    print(f"   Initial document count: {doctrine_kb.count_documents()}")
    
    # Simulate adding a PDF document
    print("\n2. Processing and adding PDF document...")
    pdf_path = "doctrine_kb/raw/ems_operations_manual.pdf"  # Simulated path
    document_name = "USAF EMS Operations Manual"
    
    added_count = add_pdf_to_doctrine_kb(pdf_path, document_name, doctrine_kb)
    print(f"   Added {added_count} document sections")
    print(f"   Total documents now: {doctrine_kb.count_documents()}")
    
    # Demonstrate agent access
    print("\n3. Agent Context Access...")
    demonstrate_agent_access(doctrine_kb)
    
    # Show direct queries
    print("\n4. Direct Doctrine Queries...")
    query_doctrine_directly(doctrine_kb)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("✓ PDF document processed and chunked into sections")
    print("✓ Document sections added to doctrine knowledge base")
    print("✓ Agents automatically receive relevant content based on role/task")
    print("✓ Semantic search finds most relevant sections for each query")
    print("✓ Access control ensures appropriate information sharing")
    print("\nThe system is ready to handle real PDF documents!")


if __name__ == "__main__":
    main()
