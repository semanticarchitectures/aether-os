# Agent Context Management Guide

## Overview

The Aether OS agent context management system provides intelligent, role-based information delivery to agents. This system ensures agents receive the most relevant information for their current tasks while respecting access control policies and optimizing context window usage.

## Architecture

### Core Components

1. **AgentContextManager** - Builds and manages context windows for agents
2. **DoctrineKnowledgeBase** - Vector-based storage for doctrine documents
3. **InformationBroker** - Centralized information access with access control
4. **AgentContext** - Multi-layered context structure for agents

### Context Structure

Each agent receives a structured context containing:

```python
@dataclass
class AgentContext:
    # Core context components
    doctrinal_context: DoctrineContext      # Relevant procedures and doctrine
    situational_context: SituationalContext # Current threats, assets, missions
    historical_context: HistoricalContext   # Past cycle performance, lessons learned
    collaborative_context: CollaborativeContext # Other agents' outputs, shared state
```

## Adding PDF Documents to the System

### Method 1: Using the PDF Integration Script

```bash
# Add a single PDF document
python scripts/add_pdf_documents.py --pdf path/to/document.pdf --name "Document Name"

# Process all PDFs in a directory
python scripts/add_pdf_documents.py --directory doctrine_kb/raw/

# List current documents
python scripts/add_pdf_documents.py --list
```

### Method 2: Programmatic Integration

```python
from aether_os.doctrine_kb import DoctrineKnowledgeBase
from scripts.add_pdf_documents import add_pdf_to_system

# Initialize doctrine knowledge base
doctrine_kb = DoctrineKnowledgeBase()

# Add a PDF document
chunks_added = add_pdf_to_system(
    pdf_path="path/to/your/document.pdf",
    document_name="EMS Operations Manual",
    doctrine_kb=doctrine_kb
)

print(f"Added {chunks_added} document chunks")
```

### Method 3: Manual Document Addition

```python
from aether_os.doctrine_kb import DoctrineKnowledgeBase

doctrine_kb = DoctrineKnowledgeBase()

# Add document content directly
success = doctrine_kb.add_document(
    document_id="UNIQUE-DOC-ID",
    content="Your document content here...",
    metadata={
        'document': 'Document Name',
        'section': 'Section 1.0',
        'source_type': 'pdf',
        'authority_level': 'Service',
        'content_type': 'doctrine',
        'applicable_roles': 'ew_planner,spectrum_manager',
    }
)
```

## How Agents Access Documents

### Automatic Context Building

Agents automatically receive relevant document content through the context system:

```python
# Agent requests context for a task
context = agent.request_context(
    task_description="Plan EW missions for target set",
    max_context_size=32000
)

# Context manager automatically:
# 1. Queries doctrine KB for relevant content
# 2. Applies access control filters
# 3. Prioritizes by relevance to task
# 4. Optimizes for context size limits

# Agent accesses doctrine content
for procedure in context.doctrinal_context.relevant_procedures:
    document = procedure['metadata']['document']
    content = procedure['content']
    relevance = procedure['relevance_score']
```

### Phase-Based Context Templates

Different agents receive different content based on their role and current ATO phase:

```python
# Phase 3 (Weaponeering) - EW Planner Agent
PHASE_CONTEXT_TEMPLATES = {
    "PHASE3_WEAPONEERING": {
        "ew_planner_agent": {
            "doctrine_priority": ["mission_planning", "asset_assignment"],
            "threat_detail_level": "tactical",
            "asset_visibility": "detailed",
            "historical_depth": 1,
        }
    }
}
```

### Access Control

Documents are filtered based on:

1. **Agent Access Level** - OPERATIONAL, SENSITIVE, CRITICAL
2. **Document Authority Level** - PUBLIC, INTERNAL, SERVICE, etc.
3. **Role Appropriateness** - Which agent roles can access the content
4. **Phase Restrictions** - Some content only available in certain phases

## Document Processing Best Practices

### 1. Document Chunking Strategy

- **By Sections**: Split documents into logical sections (chapters, procedures)
- **By Size**: Keep chunks under 2000 characters for optimal retrieval
- **Preserve Context**: Maintain section headers and context in each chunk

### 2. Metadata Design

Include comprehensive metadata for effective filtering:

```python
metadata = {
    'document': 'Document Name',           # Source document
    'section': 'Section 1.2',             # Specific section
    'source_type': 'pdf',                 # Source type
    'authority_level': 'Service',         # Required access level
    'content_type': 'doctrine',           # Content category
    'applicable_roles': 'ew_planner,spectrum_manager',  # Relevant agents
    'page_number': '15-20',               # Source page range
    'keywords': 'frequency,allocation',    # Search keywords
}
```

### 3. Content Organization

Organize documents in the `doctrine_kb/` directory:

```
doctrine_kb/
├── raw/                    # Original PDF files
│   ├── afi_10_703.pdf
│   ├── jp_3_13_1.pdf
│   └── ems_manual.pdf
├── processed/              # Processed text files
├── metadata/               # Document metadata
└── chroma_db/             # Vector database storage
```

## Context Usage Tracking

The system tracks how agents use provided context:

```python
# Track context usage
usage_stats = context_manager.track_context_usage(
    agent_id="ew_planner_agent",
    context=context,
    result={"missions_planned": 5}
)

# Get utilization statistics
stats = context_manager.get_context_statistics("ew_planner_agent")
print(f"Average utilization: {stats['avg_utilization_rate']:.1%}")
```

## Context Refresh Triggers

Context is automatically refreshed when:

1. **Phase Transitions** - New ATO phase begins
2. **New Intelligence** - Updated threat or asset information
3. **Task Changes** - Agent receives new task assignment
4. **Periodic Updates** - Regular refresh intervals
5. **Manual Refresh** - Explicitly requested

## Example: Complete Workflow

```python
from aether_os.core import AetherOS
from aether_os.orchestrator import ATOPhase

# 1. Initialize system
aether = AetherOS()

# 2. Add PDF documents (one-time setup)
from scripts.add_pdf_documents import add_pdf_to_system
add_pdf_to_system("doctrine_kb/raw/ems_manual.pdf", "EMS Operations Manual")

# 3. Register and activate agent
await aether.register_agent(ew_planner_agent)
await aether.activate_agent("ew_planner_agent")

# 4. Agent automatically gets context when performing tasks
result = await ew_planner_agent.execute_phase_tasks(
    phase="PHASE3_WEAPONEERING",
    cycle_id="ATO-001"
)

# The agent automatically received relevant sections from the PDF
# based on its role, current task, and access permissions
```

## Performance Optimization

### Context Size Management

- **Token Limits**: Default 32,000 tokens per context window
- **Pruning Strategy**: Remove historical context first, then summarize situational context
- **Relevance Scoring**: Prioritize most relevant content for the current task

### Caching and Efficiency

- **Context Caching**: Reuse context when task/phase unchanged
- **Incremental Updates**: Only refresh changed portions
- **Batch Processing**: Process multiple documents efficiently

## Troubleshooting

### Common Issues

1. **PDF Extraction Fails**
   - Install required libraries: `pip install PyPDF2 pdfplumber`
   - Try different extraction methods: `--method pdfplumber`

2. **No Relevant Content Found**
   - Check document metadata matches agent roles
   - Verify access control permissions
   - Review chunking strategy for better granularity

3. **Context Size Exceeded**
   - Reduce `max_context_size` parameter
   - Improve document chunking
   - Use more specific queries

### Debugging Context

```python
# Debug context building
context = context_manager.build_context_window(
    agent_id="ew_planner_agent",
    current_task="Plan EW missions",
    phase=ATOPhase.PHASE3_WEAPONEERING
)

print(f"Total context size: {context.total_size()} tokens")
print(f"Doctrine procedures: {len(context.doctrinal_context.relevant_procedures)}")

# Check what content was included
for proc in context.doctrinal_context.relevant_procedures:
    print(f"- {proc['metadata']['document']}: {proc['relevance_score']:.2f}")
```

## Security Considerations

1. **Access Control**: Always verify agent permissions before providing content
2. **Data Sanitization**: Remove sensitive information based on access level
3. **Audit Logging**: Track all information access for compliance
4. **Document Classification**: Properly classify all documents with authority levels

The agent context management system provides a powerful, secure, and efficient way to deliver relevant information to agents while maintaining proper access controls and optimizing performance.
