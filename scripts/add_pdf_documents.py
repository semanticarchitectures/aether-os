#!/usr/bin/env python3
"""
Add PDF Documents to Aether OS Doctrine Knowledge Base

This script provides utilities to process real PDF files and add them to the
Aether OS doctrine knowledge base for agent access.

Usage:
    python scripts/add_pdf_documents.py --pdf path/to/document.pdf --name "Document Name"
    python scripts/add_pdf_documents.py --directory doctrine_kb/raw/
    python scripts/add_pdf_documents.py --list  # Show current documents
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aether_os.doctrine_kb import DoctrineKnowledgeBase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def extract_pdf_text_pypdf2(pdf_path: str) -> str:
    """
    Extract text from PDF using PyPDF2.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1}: {e}")
                    
        return text_content
        
    except ImportError:
        logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
        return ""
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""


def extract_pdf_text_pdfplumber(pdf_path: str) -> str:
    """
    Extract text from PDF using pdfplumber (better for complex layouts).
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    try:
        import pdfplumber
        
        text_content = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num + 1}: {e}")
                    
        return text_content
        
    except ImportError:
        logger.error("pdfplumber not installed. Install with: pip install pdfplumber")
        return ""
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""


def extract_pdf_text(pdf_path: str, method: str = "auto") -> str:
    """
    Extract text from PDF using the best available method.
    
    Args:
        pdf_path: Path to the PDF file
        method: Extraction method ("auto", "pypdf2", "pdfplumber")
        
    Returns:
        Extracted text content
    """
    logger.info(f"Extracting text from PDF: {pdf_path}")
    
    if method == "auto":
        # Try pdfplumber first (better quality), fall back to PyPDF2
        text = extract_pdf_text_pdfplumber(pdf_path)
        if not text:
            text = extract_pdf_text_pypdf2(pdf_path)
    elif method == "pdfplumber":
        text = extract_pdf_text_pdfplumber(pdf_path)
    elif method == "pypdf2":
        text = extract_pdf_text_pypdf2(pdf_path)
    else:
        raise ValueError(f"Unknown extraction method: {method}")
    
    if text:
        logger.info(f"Extracted {len(text)} characters from PDF")
    else:
        logger.error("Failed to extract text from PDF")
        
    return text


def chunk_document_intelligently(text: str, document_name: str, max_chunk_size: int = 2000) -> List[Dict[str, Any]]:
    """
    Intelligently chunk a document for optimal retrieval.
    
    Args:
        text: Full document text
        document_name: Name of the source document
        max_chunk_size: Maximum size per chunk in characters
        
    Returns:
        List of document chunks with metadata
    """
    logger.info(f"Chunking document: {document_name}")
    
    chunks = []
    
    # Split by pages first
    pages = text.split("--- Page")
    
    current_chunk = ""
    chunk_number = 1
    
    for page in pages:
        if not page.strip():
            continue
            
        # Extract page number if available
        lines = page.strip().split('\n')
        page_info = lines[0] if lines else ""
        page_content = '\n'.join(lines[1:]) if len(lines) > 1 else page
        
        # If adding this page would exceed chunk size, save current chunk
        if len(current_chunk) + len(page_content) > max_chunk_size and current_chunk:
            chunk = {
                'id': f"{document_name.replace(' ', '-').upper()}-CHUNK-{chunk_number}",
                'content': current_chunk.strip(),
                'metadata': {
                    'document': document_name,
                    'section': f"Chunk {chunk_number}",
                    'source_type': 'pdf',
                    'authority_level': 'Service',
                    'content_type': 'doctrine',
                    'applicable_roles': 'ew_planner,spectrum_manager,ems_strategy,ato_producer',
                    'chunk_number': str(chunk_number),
                    'chunk_size': len(current_chunk)
                }
            }
            chunks.append(chunk)
            current_chunk = ""
            chunk_number += 1
        
        # Add page content to current chunk
        current_chunk += f"\n{page_content}\n"
    
    # Add final chunk if there's remaining content
    if current_chunk.strip():
        chunk = {
            'id': f"{document_name.replace(' ', '-').upper()}-CHUNK-{chunk_number}",
            'content': current_chunk.strip(),
            'metadata': {
                'document': document_name,
                'section': f"Chunk {chunk_number}",
                'source_type': 'pdf',
                'authority_level': 'Service',
                'content_type': 'doctrine',
                'applicable_roles': 'ew_planner,spectrum_manager,ems_strategy,ato_producer',
                'chunk_number': str(chunk_number),
                'chunk_size': len(current_chunk)
            }
        }
        chunks.append(chunk)
    
    logger.info(f"Created {len(chunks)} chunks from document")
    return chunks


def add_pdf_to_system(pdf_path: str, document_name: Optional[str] = None, 
                     doctrine_kb: Optional[DoctrineKnowledgeBase] = None) -> int:
    """
    Add a PDF document to the Aether OS system.
    
    Args:
        pdf_path: Path to the PDF file
        document_name: Name for the document (defaults to filename)
        doctrine_kb: Doctrine knowledge base instance
        
    Returns:
        Number of chunks successfully added
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return 0
    
    if document_name is None:
        document_name = Path(pdf_path).stem.replace('_', ' ').title()
    
    if doctrine_kb is None:
        doctrine_kb = DoctrineKnowledgeBase()
    
    logger.info(f"Processing PDF: {pdf_path} -> {document_name}")
    
    # Extract text from PDF
    text_content = extract_pdf_text(pdf_path)
    if not text_content:
        logger.error("Failed to extract text from PDF")
        return 0
    
    # Chunk the document
    chunks = chunk_document_intelligently(text_content, document_name)
    
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
        else:
            logger.error(f"Failed to add chunk: {chunk['id']}")
    
    logger.info(f"Successfully added {added_count}/{len(chunks)} chunks to doctrine KB")
    return added_count


def process_directory(directory_path: str, doctrine_kb: Optional[DoctrineKnowledgeBase] = None) -> int:
    """
    Process all PDF files in a directory.
    
    Args:
        directory_path: Path to directory containing PDFs
        doctrine_kb: Doctrine knowledge base instance
        
    Returns:
        Total number of chunks added
    """
    if not os.path.exists(directory_path):
        logger.error(f"Directory not found: {directory_path}")
        return 0
    
    if doctrine_kb is None:
        doctrine_kb = DoctrineKnowledgeBase()
    
    pdf_files = list(Path(directory_path).glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in: {directory_path}")
        return 0
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    total_added = 0
    for pdf_file in pdf_files:
        logger.info(f"Processing: {pdf_file.name}")
        added = add_pdf_to_system(str(pdf_file), doctrine_kb=doctrine_kb)
        total_added += added
    
    logger.info(f"Processed {len(pdf_files)} files, added {total_added} total chunks")
    return total_added


def list_documents(doctrine_kb: Optional[DoctrineKnowledgeBase] = None):
    """
    List all documents in the doctrine knowledge base.

    Args:
        doctrine_kb: Doctrine knowledge base instance
    """
    if doctrine_kb is None:
        doctrine_kb = DoctrineKnowledgeBase()

    count = doctrine_kb.count_documents()
    print(f"\nDoctrine Knowledge Base contains {count} documents")

    if count > 0:
        # Try to get some sample documents using a simple query
        try:
            # Use a broad query to get sample documents
            results = doctrine_kb.query("doctrine", top_k=10)

            if results:
                print("\nSample documents:")
                documents = {}
                for result in results:
                    doc_name = result.get('metadata', {}).get('document', 'Unknown')
                    section = result.get('metadata', {}).get('section', 'Unknown')
                    if doc_name not in documents:
                        documents[doc_name] = []
                    documents[doc_name].append(section)

                for doc_name, sections in documents.items():
                    print(f"  • {doc_name} ({len(sections)} sections)")
                    for section in sections[:3]:  # Show first 3 sections
                        print(f"    - {section}")
                    if len(sections) > 3:
                        print(f"    ... and {len(sections) - 3} more sections")

        except Exception as e:
            logger.warning(f"Could not retrieve document list: {e}")
            print("  (Unable to retrieve document details)")


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description="Add PDF documents to Aether OS")
    parser.add_argument("--pdf", help="Path to PDF file to add")
    parser.add_argument("--name", help="Name for the document")
    parser.add_argument("--directory", help="Directory containing PDF files")
    parser.add_argument("--list", action="store_true", help="List current documents")
    parser.add_argument("--method", choices=["auto", "pypdf2", "pdfplumber"], 
                       default="auto", help="PDF extraction method")
    
    args = parser.parse_args()
    
    # Initialize doctrine knowledge base
    doctrine_kb = DoctrineKnowledgeBase()
    
    if args.list:
        list_documents(doctrine_kb)
    elif args.pdf:
        add_pdf_to_system(args.pdf, args.name, doctrine_kb)
        list_documents(doctrine_kb)
    elif args.directory:
        process_directory(args.directory, doctrine_kb)
        list_documents(doctrine_kb)
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python scripts/add_pdf_documents.py --pdf doctrine_kb/raw/manual.pdf --name 'EMS Manual'")
        print("  python scripts/add_pdf_documents.py --directory doctrine_kb/raw/")
        print("  python scripts/add_pdf_documents.py --list")


if __name__ == "__main__":
    main()
