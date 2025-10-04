#!/usr/bin/env python3
"""
Document Source Tracker for Aether OS

This script provides comprehensive tracking of source files used to populate
the vector database, including logging, metadata, and audit trails.

Usage:
    python scripts/document_source_tracker.py --add-pdf path/to/file.pdf
    python scripts/document_source_tracker.py --show-sources
    python scripts/document_source_tracker.py --audit-log
"""

import os
import sys
import json
import hashlib
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aether_os.doctrine_kb import DoctrineKnowledgeBase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Source tracking configuration
SOURCE_LOG_FILE = "doctrine_kb/metadata/source_tracking.json"
PROCESSING_LOG_FILE = "doctrine_kb/metadata/processing.log"


class DocumentSourceTracker:
    """Tracks source files and processing history for the doctrine knowledge base."""
    
    def __init__(self):
        """Initialize the source tracker."""
        self.source_log_path = Path(SOURCE_LOG_FILE)
        self.processing_log_path = Path(PROCESSING_LOG_FILE)
        
        # Ensure metadata directory exists
        self.source_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up processing log
        self._setup_processing_log()
        
        # Load existing source tracking data
        self.source_data = self._load_source_data()
    
    def _setup_processing_log(self):
        """Set up the processing log file."""
        # Add file handler for processing log
        file_handler = logging.FileHandler(self.processing_log_path)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add to logger
        processing_logger = logging.getLogger('document_processing')
        processing_logger.addHandler(file_handler)
        processing_logger.setLevel(logging.INFO)
        
        self.processing_logger = processing_logger
    
    def _load_source_data(self) -> Dict[str, Any]:
        """Load existing source tracking data."""
        if self.source_log_path.exists():
            try:
                with open(self.source_log_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load source data: {e}")
                return {"documents": {}, "processing_history": []}
        else:
            return {"documents": {}, "processing_history": []}
    
    def _save_source_data(self):
        """Save source tracking data to file."""
        try:
            with open(self.source_log_path, 'w') as f:
                json.dump(self.source_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save source data: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Could not calculate hash for {file_path}: {e}")
            return "unknown"
    
    def track_pdf_processing(
        self, 
        pdf_path: str, 
        document_name: str,
        chunks_added: int,
        processing_method: str = "auto",
        user: Optional[str] = None
    ) -> str:
        """
        Track the processing of a PDF file.
        
        Args:
            pdf_path: Path to the source PDF file
            document_name: Name assigned to the document
            chunks_added: Number of chunks successfully added
            processing_method: Method used for PDF extraction
            user: User who processed the document
            
        Returns:
            Processing ID for this operation
        """
        processing_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.source_data['processing_history'])}"
        
        # Calculate file hash for integrity verification
        file_hash = self._calculate_file_hash(pdf_path)
        file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
        
        # Create processing record
        processing_record = {
            "processing_id": processing_id,
            "timestamp": datetime.now().isoformat(),
            "source_file": os.path.abspath(pdf_path),
            "document_name": document_name,
            "file_hash": file_hash,
            "file_size": file_size,
            "processing_method": processing_method,
            "chunks_added": chunks_added,
            "user": user or os.getenv('USER', 'unknown'),
            "status": "completed" if chunks_added > 0 else "failed"
        }
        
        # Add to processing history
        self.source_data["processing_history"].append(processing_record)
        
        # Update document registry
        if document_name not in self.source_data["documents"]:
            self.source_data["documents"][document_name] = {
                "source_files": [],
                "total_chunks": 0,
                "last_updated": None
            }
        
        # Add source file info
        source_file_info = {
            "file_path": os.path.abspath(pdf_path),
            "file_hash": file_hash,
            "processing_id": processing_id,
            "chunks_added": chunks_added,
            "timestamp": datetime.now().isoformat()
        }
        
        self.source_data["documents"][document_name]["source_files"].append(source_file_info)
        self.source_data["documents"][document_name]["total_chunks"] += chunks_added
        self.source_data["documents"][document_name]["last_updated"] = datetime.now().isoformat()
        
        # Log the processing
        self.processing_logger.info(
            f"PDF processed: {pdf_path} -> {document_name} "
            f"({chunks_added} chunks, method: {processing_method}, hash: {file_hash[:8]}...)"
        )
        
        # Save updated data
        self._save_source_data()
        
        return processing_id
    
    def get_document_sources(self, document_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get source information for documents.
        
        Args:
            document_name: Specific document name, or None for all documents
            
        Returns:
            Dictionary with source information
        """
        if document_name:
            return self.source_data["documents"].get(document_name, {})
        else:
            return self.source_data["documents"]
    
    def get_processing_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get processing history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of processing records
        """
        history = self.source_data["processing_history"]
        if limit:
            return history[-limit:]
        return history
    
    def verify_file_integrity(self, document_name: str) -> Dict[str, Any]:
        """
        Verify integrity of source files for a document.
        
        Args:
            document_name: Name of the document to verify
            
        Returns:
            Verification results
        """
        if document_name not in self.source_data["documents"]:
            return {"error": f"Document '{document_name}' not found in registry"}
        
        doc_info = self.source_data["documents"][document_name]
        verification_results = {
            "document_name": document_name,
            "total_source_files": len(doc_info["source_files"]),
            "files_verified": 0,
            "files_missing": 0,
            "files_modified": 0,
            "details": []
        }
        
        for source_file in doc_info["source_files"]:
            file_path = source_file["file_path"]
            original_hash = source_file["file_hash"]
            
            file_result = {
                "file_path": file_path,
                "status": "unknown",
                "original_hash": original_hash,
                "current_hash": None
            }
            
            if not os.path.exists(file_path):
                file_result["status"] = "missing"
                verification_results["files_missing"] += 1
            else:
                current_hash = self._calculate_file_hash(file_path)
                file_result["current_hash"] = current_hash
                
                if current_hash == original_hash:
                    file_result["status"] = "verified"
                    verification_results["files_verified"] += 1
                else:
                    file_result["status"] = "modified"
                    verification_results["files_modified"] += 1
            
            verification_results["details"].append(file_result)
        
        return verification_results
    
    def generate_audit_report(self) -> str:
        """Generate a comprehensive audit report."""
        report_lines = [
            "=== DOCTRINE KNOWLEDGE BASE AUDIT REPORT ===",
            f"Generated: {datetime.now().isoformat()}",
            ""
        ]
        
        # Summary statistics
        total_docs = len(self.source_data["documents"])
        total_processing = len(self.source_data["processing_history"])
        
        report_lines.extend([
            "SUMMARY:",
            f"  Total documents: {total_docs}",
            f"  Total processing operations: {total_processing}",
            ""
        ])
        
        # Document registry
        report_lines.extend([
            "DOCUMENT REGISTRY:",
            "-" * 20
        ])
        
        for doc_name, doc_info in self.source_data["documents"].items():
            total_chunks = doc_info["total_chunks"]
            source_count = len(doc_info["source_files"])
            last_updated = doc_info["last_updated"]
            
            report_lines.extend([
                f"📄 {doc_name}",
                f"   Total chunks: {total_chunks}",
                f"   Source files: {source_count}",
                f"   Last updated: {last_updated}",
                ""
            ])
            
            for source_file in doc_info["source_files"]:
                file_path = source_file["file_path"]
                chunks = source_file["chunks_added"]
                timestamp = source_file["timestamp"]
                file_hash = source_file["file_hash"][:8]
                
                report_lines.append(f"     • {file_path} ({chunks} chunks, {timestamp}, hash: {file_hash}...)")
            
            report_lines.append("")
        
        # Recent processing history
        report_lines.extend([
            "RECENT PROCESSING HISTORY:",
            "-" * 27
        ])
        
        recent_history = self.get_processing_history(limit=10)
        for record in reversed(recent_history):
            timestamp = record["timestamp"]
            source_file = record["source_file"]
            document_name = record["document_name"]
            chunks = record["chunks_added"]
            status = record["status"]
            method = record["processing_method"]
            
            report_lines.append(
                f"{timestamp}: {source_file} -> {document_name} "
                f"({chunks} chunks, {method}, {status})"
            )
        
        return "\n".join(report_lines)


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description="Track document sources for Aether OS")
    parser.add_argument("--add-pdf", help="Add PDF and track source")
    parser.add_argument("--name", help="Document name for PDF")
    parser.add_argument("--show-sources", action="store_true", help="Show document sources")
    parser.add_argument("--audit-log", action="store_true", help="Generate audit report")
    parser.add_argument("--verify", help="Verify integrity of document sources")
    parser.add_argument("--history", type=int, help="Show processing history (last N entries)")
    
    args = parser.parse_args()
    
    # Initialize tracker
    tracker = DocumentSourceTracker()
    
    if args.add_pdf:
        # Add PDF with source tracking
        from scripts.add_pdf_documents import add_pdf_to_system
        
        document_name = args.name or Path(args.add_pdf).stem.replace('_', ' ').title()
        
        print(f"Processing PDF: {args.add_pdf}")
        print(f"Document name: {document_name}")
        
        # Process the PDF
        chunks_added = add_pdf_to_system(args.add_pdf, document_name)
        
        # Track the processing
        processing_id = tracker.track_pdf_processing(
            pdf_path=args.add_pdf,
            document_name=document_name,
            chunks_added=chunks_added,
            processing_method="auto"
        )
        
        print(f"Processing ID: {processing_id}")
        print(f"Chunks added: {chunks_added}")
        
    elif args.show_sources:
        # Show document sources
        sources = tracker.get_document_sources()
        
        print("=== DOCUMENT SOURCES ===")
        for doc_name, doc_info in sources.items():
            print(f"\n📄 {doc_name}")
            print(f"   Total chunks: {doc_info['total_chunks']}")
            print(f"   Last updated: {doc_info['last_updated']}")
            print(f"   Source files:")
            
            for source_file in doc_info['source_files']:
                file_path = source_file['file_path']
                chunks = source_file['chunks_added']
                timestamp = source_file['timestamp']
                print(f"     • {file_path} ({chunks} chunks, {timestamp})")
    
    elif args.audit_log:
        # Generate audit report
        report = tracker.generate_audit_report()
        print(report)
        
        # Also save to file
        report_file = f"doctrine_kb/metadata/audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\nAudit report saved to: {report_file}")
    
    elif args.verify:
        # Verify document integrity
        results = tracker.verify_file_integrity(args.verify)
        
        print(f"=== INTEGRITY VERIFICATION: {args.verify} ===")
        if "error" in results:
            print(f"Error: {results['error']}")
        else:
            print(f"Total source files: {results['total_source_files']}")
            print(f"Files verified: {results['files_verified']}")
            print(f"Files missing: {results['files_missing']}")
            print(f"Files modified: {results['files_modified']}")
            
            for detail in results['details']:
                status = detail['status']
                file_path = detail['file_path']
                
                if status == "verified":
                    print(f"✅ {file_path}")
                elif status == "missing":
                    print(f"❌ {file_path} (MISSING)")
                elif status == "modified":
                    print(f"⚠️  {file_path} (MODIFIED)")
    
    elif args.history:
        # Show processing history
        history = tracker.get_processing_history(limit=args.history)
        
        print(f"=== PROCESSING HISTORY (Last {len(history)} entries) ===")
        for record in reversed(history):
            timestamp = record['timestamp']
            source_file = record['source_file']
            document_name = record['document_name']
            chunks = record['chunks_added']
            status = record['status']
            
            print(f"{timestamp}: {source_file}")
            print(f"  -> {document_name} ({chunks} chunks, {status})")
    
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python scripts/document_source_tracker.py --add-pdf manual.pdf --name 'EMS Manual'")
        print("  python scripts/document_source_tracker.py --show-sources")
        print("  python scripts/document_source_tracker.py --audit-log")
        print("  python scripts/document_source_tracker.py --verify 'EMS Manual'")


if __name__ == "__main__":
    main()
