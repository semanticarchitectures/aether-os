#!/usr/bin/env python3
"""
Seed Test Data

Populates doctrine knowledge base and databases with sample test data.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aether_os.doctrine_kb import DoctrineKnowledgeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_doctrine_kb():
    """Seed doctrine knowledge base with sample doctrine."""
    logger.info("Seeding doctrine knowledge base...")

    doctrine_kb = DoctrineKnowledgeBase()

    # Sample doctrine documents
    doctrine_docs = [
        {
            "id": "AFI-10-703-S1",
            "content": (
                "EMS Strategy Development: The EMS strategy must be derived from "
                "the Joint Force Air Component Commander (JFACC) guidance and "
                "synchronized with the overall air component strategy. Key elements "
                "include: (1) Commander's EMS Intent, (2) EMS Objectives, "
                "(3) Desired EMS Effects, (4) EMS Concept of Operations."
            ),
            "metadata": {
                "document": "AFI 10-703",
                "section": "3.1",
                "authority_level": "Service",
                "content_type": "procedure",
                "applicable_roles": ["ems_strategy"],
            },
        },
        {
            "id": "AFI-10-703-S2",
            "content": (
                "Spectrum Management: All frequency allocations must be coordinated "
                "through the Joint Communications-Electronics Operating Instructions "
                "(JCEOI) process. Deconfliction is required with: (1) Other EMS users, "
                "(2) Friendly radar systems, (3) SIGINT collection operations. "
                "Emergency reallocations during execution require O-5 or higher approval."
            ),
            "metadata": {
                "document": "AFI 10-703",
                "section": "4.2",
                "authority_level": "Service",
                "content_type": "procedure",
                "applicable_roles": ["spectrum_manager"],
            },
        },
        {
            "id": "AFI-10-703-S3",
            "content": (
                "EW Mission Planning: Electronic Warfare missions must integrate "
                "Electronic Attack (EA), Electronic Protection (EP), and Electronic "
                "Warfare Support (ES) operations. Planners must: (1) Assign appropriate "
                "EMS assets, (2) Request frequency allocations, (3) Check for EA/SIGINT "
                "fratricide, (4) Coordinate with kinetic strike packages."
            ),
            "metadata": {
                "document": "AFI 10-703",
                "section": "5.3",
                "authority_level": "Service",
                "content_type": "procedure",
                "applicable_roles": ["ew_planner"],
            },
        },
        {
            "id": "AFI-10-703-S4",
            "content": (
                "ATO Integration: EMS operations must be integrated into the Air "
                "Tasking Order (ATO) through the EMS Annex and Special Instructions "
                "(SPINS). The ATO Producer must: (1) Validate mission approvals, "
                "(2) Integrate EMS with kinetic operations, (3) Generate SPINS for "
                "EMS procedures, (4) Ensure deconfliction with other operations."
            ),
            "metadata": {
                "document": "AFI 10-703",
                "section": "6.1",
                "authority_level": "Service",
                "content_type": "procedure",
                "applicable_roles": ["ato_producer"],
            },
        },
        {
            "id": "AFI-10-703-S5",
            "content": (
                "Assessment and Lessons Learned: Post-execution assessment must "
                "evaluate: (1) Mission effectiveness, (2) Timeline adherence, "
                "(3) Coordination effectiveness, (4) Process improvements. "
                "Documented lessons learned must be shared across the community."
            ),
            "metadata": {
                "document": "AFI 10-703",
                "section": "7.2",
                "authority_level": "Service",
                "content_type": "procedure",
                "applicable_roles": ["assessment"],
            },
        },
        {
            "id": "JP-3-13.1-EMS",
            "content": (
                "EMS Operations Fundamentals: The electromagnetic spectrum is a "
                "maneuver space that enables information collection, communication, "
                "position/navigation/timing, and weapons employment. EMS superiority "
                "requires denying adversary use while ensuring friendly freedom of action."
            ),
            "metadata": {
                "document": "JP 3-13.1",
                "section": "1.1",
                "authority_level": "Joint",
                "content_type": "doctrine",
                "applicable_roles": ["ems_strategy", "ew_planner"],
            },
        },
    ]

    # Add documents to knowledge base
    count = doctrine_kb.add_documents_batch(doctrine_docs)

    logger.info(f"Added {count} doctrine documents to knowledge base")
    logger.info(f"Total documents in KB: {doctrine_kb.count_documents()}")


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("AETHER OS - SEED TEST DATA")
    logger.info("=" * 60)

    # Seed doctrine KB
    seed_doctrine_kb()

    logger.info("\nTest data seeding complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
