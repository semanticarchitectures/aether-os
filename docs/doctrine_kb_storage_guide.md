# Doctrine Knowledge Base Storage Guide

## Overview

The Doctrine Knowledge Base stores documents using **ChromaDB**, a vector database that enables semantic search through document embeddings. This guide explains where documents are stored, how the storage works, and how to manage the stored data.

## Storage Locations

### Primary Storage Directory

```
📁 /Users/kevinkelly/aether-project/doctrine_kb/
├── 📁 raw/                    # Original PDF files (input)
├── 📁 processed/              # Processed text files (intermediate)
├── 📁 metadata/               # Document metadata (optional)
└── 📁 chroma_db/              # Vector database storage (ChromaDB)
    ├── 📄 chroma.sqlite3      # Main database file (224 KB)
    └── 📁 [uuid-directory]/   # Vector embeddings and indexes
        ├── 📄 data_level0.bin # Vector data (163.7 KB)
        ├── 📄 header.bin      # Index headers (100 bytes)
        ├── 📄 length.bin      # Vector lengths (400 bytes)
        └── 📄 link_lists.bin  # Hierarchical index (0 bytes)
```

### Configuration

The storage location is configured in `aether_os/doctrine_kb.py`:

```python
def __init__(self, persist_directory: Optional[str] = None):
    self.persist_directory = persist_directory or os.path.join(
        os.getcwd(), "doctrine_kb", "chroma_db"
    )
```

**Default location**: `{project_root}/doctrine_kb/chroma_db/`

## What's Stored

### Document Content

Currently stored documents (7 total):

1. **USAF EMS Operations Manual** (4 sections, 1,588 characters)
   - Source: PDF simulation
   - Sections: Strategic Planning, Frequency Management, Mission Execution
   - Authority Level: Service
   - Applicable Roles: ew_planner, spectrum_manager, ems_strategy

2. **EMS Operations Planning Guide** (3 sections, 981 characters)
   - Source: PDF simulation  
   - Sections: Strategic Planning, Frequency Management, Mission Execution
   - Authority Level: Service
   - Applicable Roles: spectrum_manager, ew_planner, ato_producer

### Storage Format

Each document is stored as:

```python
{
    'id': 'UNIQUE-DOCUMENT-ID',
    'content': 'Full text content of the document section...',
    'metadata': {
        'document': 'Document Name',
        'section': 'Section 1.0',
        'source_type': 'pdf',
        'authority_level': 'Service',
        'content_type': 'doctrine',
        'applicable_roles': 'ew_planner,spectrum_manager',
        'page_number': '1-5',
        'chunk_number': '1'
    },
    'embeddings': [0.123, -0.456, 0.789, ...]  # High-dimensional vector
}
```

## Storage Technology

### ChromaDB Architecture

- **Vector Database**: ChromaDB with persistent storage
- **Embeddings**: Default sentence-transformers model
- **Persistence**: SQLite database + binary vector files
- **Search Method**: Semantic similarity using cosine distance
- **Collection**: Single "doctrine" collection for all documents

### File Breakdown

1. **chroma.sqlite3** (224 KB)
   - Main database file
   - Stores metadata, document IDs, collection info
   - SQLite format for reliability and ACID compliance

2. **UUID Directory** (e.g., `7fb2eef6-5f58-48fd-9619-a1c4f9f6a9c0/`)
   - Contains vector index files
   - One directory per collection
   - Binary format for fast vector operations

3. **Vector Files**:
   - `data_level0.bin` (163.7 KB) - Actual vector embeddings
   - `header.bin` (100 bytes) - Index metadata
   - `length.bin` (400 bytes) - Vector dimension info
   - `link_lists.bin` (0 bytes) - Hierarchical navigation structure

## Accessing Stored Data

### Programmatic Access

```python
from aether_os.doctrine_kb import DoctrineKnowledgeBase

# Initialize (connects to existing storage)
doctrine_kb = DoctrineKnowledgeBase()

# Check storage status
print(f"Storage location: {doctrine_kb.persist_directory}")
print(f"Document count: {doctrine_kb.count_documents()}")

# Semantic search
results = doctrine_kb.query("frequency allocation procedures", top_k=5)

# Get specific procedure
procedure = doctrine_kb.get_procedure("JCEOI process")

# Search by metadata
docs = doctrine_kb.search_by_metadata({"document": "USAF EMS Operations Manual"})
```

### Command Line Tools

```bash
# List current documents
python scripts/add_pdf_documents.py --list

# Add new PDF
python scripts/add_pdf_documents.py --pdf path/to/document.pdf --name "Document Name"

# Process directory of PDFs
python scripts/add_pdf_documents.py --directory doctrine_kb/raw/
```

## Data Persistence

### Automatic Persistence

- **ChromaDB automatically persists** all data to disk
- **No manual save required** - changes are immediately written
- **ACID compliance** through SQLite ensures data integrity
- **Crash recovery** - database remains consistent even after unexpected shutdown

### Backup and Migration

```bash
# Backup the entire knowledge base
cp -r doctrine_kb/chroma_db/ backup/doctrine_kb_backup_$(date +%Y%m%d)/

# Restore from backup
rm -rf doctrine_kb/chroma_db/
cp -r backup/doctrine_kb_backup_20241204/ doctrine_kb/chroma_db/

# Move to different location
mv doctrine_kb/chroma_db/ /new/location/
# Update persist_directory in code or pass as parameter
```

## Storage Management

### Monitoring Storage Size

```python
import os
from pathlib import Path

def get_storage_size(path):
    """Get total size of storage directory."""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size

# Check current storage size
storage_path = "doctrine_kb/chroma_db"
size_bytes = get_storage_size(storage_path)
size_mb = size_bytes / (1024 * 1024)
print(f"Storage size: {size_mb:.1f} MB")
```

### Cleaning Up Storage

```python
# Delete specific documents
doctrine_kb.delete_document("DOCUMENT-ID")

# Clear entire collection (careful!)
if doctrine_kb.collection:
    doctrine_kb.client.delete_collection("doctrine")
```

## Performance Considerations

### Storage Scaling

- **Current size**: ~400 KB for 7 documents
- **Estimated scaling**: ~50-100 KB per document chunk
- **Large deployments**: Consider sharding across multiple collections
- **Memory usage**: ChromaDB loads indexes into memory for fast search

### Optimization Tips

1. **Chunk Size**: Keep document chunks under 2000 characters
2. **Metadata**: Use consistent metadata schemas for efficient filtering
3. **Batch Operations**: Use `add_documents_batch()` for multiple documents
4. **Index Tuning**: ChromaDB automatically optimizes indexes

## Security and Access Control

### File System Security

- **Directory permissions**: Ensure appropriate read/write access
- **Backup security**: Encrypt backups if they contain sensitive data
- **Network access**: ChromaDB storage is local-only by default

### Data Classification

Documents are classified by `authority_level` in metadata:
- `PUBLIC` - Publicly available information
- `INTERNAL` - Internal organizational use
- `OPERATIONAL` - Operational personnel only
- `SENSITIVE` - Restricted operational data
- `CRITICAL` - Mission-critical information

## Troubleshooting

### Common Issues

1. **Database locked**
   ```
   Error: database is locked
   Solution: Ensure no other processes are accessing the database
   ```

2. **Permission denied**
   ```
   Error: Permission denied accessing chroma_db/
   Solution: Check file system permissions
   ```

3. **Corrupted database**
   ```
   Error: database disk image is malformed
   Solution: Restore from backup or reinitialize
   ```

### Recovery Procedures

```python
# Reinitialize corrupted database
import shutil
shutil.rmtree("doctrine_kb/chroma_db/")
doctrine_kb = DoctrineKnowledgeBase()  # Creates new empty database

# Re-add documents from source
python scripts/add_pdf_documents.py --directory doctrine_kb/raw/
```

## Integration with Agents

### Automatic Access

Agents automatically access stored documents through the context system:

1. **Agent requests context** for a specific task
2. **Context manager queries** the doctrine knowledge base
3. **Semantic search** finds relevant document sections
4. **Access control** filters results based on agent permissions
5. **Optimized context** is provided to the agent

### Context Flow

```
Agent Task → Context Manager → Doctrine KB → Vector Search → 
Access Control → Filtered Results → Agent Context
```

The storage system is transparent to agents - they simply receive relevant document content through their context windows without needing to know about the underlying ChromaDB storage.

## Summary

- **Location**: `doctrine_kb/chroma_db/` directory
- **Technology**: ChromaDB vector database with SQLite persistence
- **Content**: 7 documents (2,569 total characters) stored as vector embeddings
- **Access**: Semantic search through Python API or command-line tools
- **Persistence**: Automatic with ACID compliance
- **Security**: File system permissions + metadata-based access control

The storage system provides fast, reliable, and scalable document storage with semantic search capabilities for the Aether OS agent context management system.
