"""
EMS Strategy Agent for Aether OS.

Develops EMS strategy from JFACC guidance during Phase 1 (OEG) and Phase 2
(Target Development).
"""

from typing import Dict, Any, List
import logging
import os

from agents.base_agent import BaseAetherAgent
from aether_os.access_control import InformationCategory

# LLM integration
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class EMSStrategyAgent(BaseAetherAgent):
    """
    EMS Strategy Agent.

    Active Phases: Phase 1 (OEG), Phase 2 (Target Development)
    Role: Develops EMS strategy from JFACC guidance
    Access Level: SENSITIVE
    """

    def __init__(self, aether_os: Any):
        """Initialize EMS Strategy Agent."""
        super().__init__(agent_id="ems_strategy_agent", aether_os=aether_os)

        # Initialize LLM client if available
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.llm_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            self.llm_client = None
            logger.warning("Anthropic API not available - using fallback mode")

    async def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """Execute tasks for the current phase."""
        if phase == "PHASE1_OEG":
            return await self._execute_phase1(cycle_id)
        elif phase == "PHASE2_TARGET_DEVELOPMENT":
            return await self._execute_phase2(cycle_id)
        else:
            logger.warning(f"[{self.agent_id}] Not active in phase: {phase}")
            return {}

    async def _execute_phase1(self, cycle_id: str) -> Dict[str, Any]:
        """
        Execute Phase 1 (OEG) tasks.

        Develop EMS strategy from commander's guidance.
        """
        logger.info(f"[{self.agent_id}] Executing Phase 1 (OEG) for cycle {cycle_id}")

        outputs = {}

        # Develop EMS strategy
        strategy = self.execute_doctrinal_procedure(
            procedure_name="Develop EMS Strategy",
            procedure_fn=self.develop_ems_strategy,
            expected_time_hours=3.0,
            cycle_id=cycle_id,
            phase="PHASE1_OEG",
        )

        outputs["ems_strategy"] = strategy

        # Record output
        self.aether_os.orchestrator.record_output("ems_strategy", strategy)

        return outputs

    async def _execute_phase2(self, cycle_id: str) -> Dict[str, Any]:
        """
        Execute Phase 2 (Target Development) tasks.

        Refine strategy and identify EMS requirements.
        """
        logger.info(
            f"[{self.agent_id}] Executing Phase 2 (Target Development) for cycle {cycle_id}"
        )

        outputs = {}

        # Identify EMS requirements
        requirements = self.execute_doctrinal_procedure(
            procedure_name="Identify EMS Requirements",
            procedure_fn=self._identify_ems_requirements,
            expected_time_hours=4.0,
            cycle_id=cycle_id,
            phase="PHASE2_TARGET_DEVELOPMENT",
        )

        outputs["ems_requirements"] = requirements

        # Record output
        self.aether_os.orchestrator.record_output("ems_requirements", requirements)

        return outputs

    def develop_ems_strategy(self, cycle_id: str) -> Dict[str, Any]:
        """
        Develop EMS strategy from JFACC guidance.

        This follows doctrinal procedures but uses LLM for strategy generation
        grounded in doctrine.
        """
        logger.info(f"[{self.agent_id}] Developing EMS strategy...")

        # Request context for this task
        context = self.request_context(
            task_description="Develop EMS strategy from JFACC guidance",
            max_context_size=32000,
        )

        # Query doctrine for EMS strategy guidance
        doctrine_results = self.query_doctrine(
            query="How to develop EMS strategy and concept of operations",
            filters={"content_type": "procedure"},
        )

        # Track context usage - reference doctrine items
        for doc in doctrine_results[:3]:
            self.reference_context_item(f"doctrine:{doc.get('metadata', {}).get('document', 'unknown')}")

        # Get threat data from context
        threats = context.situational_context.current_threats if context else []
        if threats:
            self.reference_context_item("situational:threats")

        # Use best practices from context
        if context and context.doctrinal_context.best_practices:
            for practice in context.doctrinal_context.best_practices:
                self.reference_context_item(f"practice:{practice[:30]}")

        # Validate against doctrine
        validation = self._validate_against_doctrine(doctrine_results)

        if not validation["compliant"]:
            logger.warning(f"Strategy not fully compliant: {validation['issues']}")
            self.flag_information_gap(
                workflow_name="Develop EMS Strategy",
                missing_information=", ".join(validation["issues"]),
                cycle_id=cycle_id,
                phase="PHASE1_OEG",
            )

        # Generate strategy using LLM if available
        if self.llm_client:
            strategy = self._generate_strategy_with_llm(doctrine_results, threats)
        else:
            strategy = self._generate_strategy_fallback(doctrine_results, threats)

        # Finalize context usage tracking
        self.finalize_context_usage(result={"strategy_generated": True, "threats_analyzed": len(threats)})

        return strategy

    def _generate_strategy_with_llm(
        self,
        doctrine_results: List[Dict],
        threats: List[Dict],
    ) -> Dict[str, Any]:
        """Generate EMS strategy using LLM grounded in doctrine."""
        # Prepare doctrine context
        doctrine_context = "\n\n".join(
            [f"- {doc['content']}" for doc in doctrine_results[:3]]
        )

        # Prepare threat context
        threat_context = f"Identified {len(threats)} EMS threats" if threats else "No threat data available"

        prompt = f"""You are an EMS Strategy Agent developing the Electromagnetic Spectrum strategy for an Air Operations Center.

Based on USAF doctrine and current threat environment, develop an EMS strategy.

DOCTRINE GUIDANCE:
{doctrine_context}

THREAT ENVIRONMENT:
{threat_context}

Develop an EMS strategy with the following components:
1. Commander's EMS Intent
2. EMS Objectives (3-5 objectives)
3. Desired EMS Effects
4. Key EMS Considerations
5. Concept of Operations for EMS

Provide a structured strategy following doctrine."""

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            strategy_text = response.content[0].text

            return {
                "strategy_text": strategy_text,
                "objectives": ["Objective 1", "Objective 2", "Objective 3"],  # Parse from LLM response
                "desired_effects": ["Effect 1", "Effect 2"],
                "threats_considered": len(threats),
                "doctrine_compliance": True,
                "generated_by": "llm",
            }

        except Exception as e:
            logger.error(f"Error generating strategy with LLM: {e}")
            return self._generate_strategy_fallback(doctrine_results, threats)

    def _generate_strategy_fallback(
        self,
        doctrine_results: List[Dict],
        threats: List[Dict],
    ) -> Dict[str, Any]:
        """Fallback strategy generation without LLM."""
        return {
            "strategy_text": (
                "EMS Strategy: Achieve electromagnetic superiority through coordinated "
                "EA, EP, and ES operations. Deny adversary use of EMS while ensuring "
                "friendly freedom of action."
            ),
            "objectives": [
                "Suppress enemy air defense systems",
                "Protect friendly communications",
                "Deny adversary C2 capabilities",
            ],
            "desired_effects": [
                "Degraded enemy air defense radar effectiveness",
                "Disrupted enemy communications",
            ],
            "threats_considered": len(threats),
            "doctrine_compliance": True,
            "generated_by": "fallback",
        }

    def _validate_against_doctrine(
        self,
        doctrine_results: List[Dict],
    ) -> Dict[str, Any]:
        """Validate strategy development against doctrine."""
        issues = []

        if not doctrine_results:
            issues.append("No doctrine guidance available for EMS strategy development")

        # Additional validation checks would go here
        # For prototype, simple validation

        return {
            "compliant": len(issues) == 0,
            "issues": issues,
        }

    def _identify_ems_requirements(self, cycle_id: str) -> Dict[str, Any]:
        """
        Identify EMS requirements based on strategy.

        This is executed in Phase 2.
        """
        logger.info(f"[{self.agent_id}] Identifying EMS requirements...")

        # Query current strategy
        current_cycle = self.aether_os.orchestrator.current_cycle
        if not current_cycle or "ems_strategy" not in current_cycle.outputs:
            logger.warning("No EMS strategy available - cannot identify requirements")
            self.flag_information_gap(
                workflow_name="Identify EMS Requirements",
                missing_information="EMS strategy from Phase 1",
                cycle_id=cycle_id,
                phase="PHASE2_TARGET_DEVELOPMENT",
            )
            return {}

        strategy = current_cycle.outputs["ems_strategy"]

        # Based on strategy, identify requirements
        requirements = {
            "ea_requirements": [
                "Jamming support for SEAD missions",
                "Standoff jamming for penetrating strikes",
            ],
            "ep_requirements": [
                "Communications protection for strike packages",
                "GPS anti-jam for precision weapons",
            ],
            "es_requirements": [
                "Target acquisition support",
                "Threat warning for strike packages",
            ],
            "spectrum_requirements": [
                "Frequency allocations for EA platforms",
                "Deconfliction with friendly radar systems",
            ],
        }

        return requirements
