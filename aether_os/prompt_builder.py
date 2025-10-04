"""
Prompt Builder for Aether OS.

Template-based prompt construction with context injection,
role-specific instructions, and output schema formatting.
"""

import logging
from typing import Dict, Any, Optional
from string import Template

from aether_os.context_processor import ProcessedContext

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Builds prompts for LLM agents with context injection.

    Features:
    - Template-based construction
    - Role-specific instructions
    - Context formatting
    - Output schema specification
    """

    # Base system prompt for all agents
    BASE_SYSTEM_PROMPT = """You are an AI agent in the USAF Air Operations Center (AOC) supporting Electromagnetic Spectrum (EMS) Operations.

Your role is to assist with ATO (Air Tasking Order) cycle operations while strictly adhering to USAF doctrine and procedures.

CRITICAL REQUIREMENTS:
1. Ground ALL decisions in provided doctrinal context
2. Cite specific context elements using their IDs (e.g., [DOC-001], [THR-001])
3. Flag information gaps - if you need info not provided, explicitly state it
4. Follow procedures exactly as documented
5. Never invent or hallucinate doctrine
6. Maintain operational security and need-to-know principles

When referencing context:
- Use the bracketed IDs: [DOC-PROC-001], [THR-001], [AST-001], etc.
- List all citations in your final response
- If context is insufficient, state what's missing
"""

    # Role-specific prompts
    ROLE_PROMPTS = {
        "ems_strategy": """ROLE: EMS Strategy Agent

You develop electromagnetic spectrum strategy during Phases 1-2 of the ATO cycle.

Your responsibilities:
- Interpret commander's intent for EMS operations
- Develop EMS concept of operations
- Identify EMS objectives and desired effects
- Consider EA (Electronic Attack), EP (Electronic Protection), and ES (Electronic Warfare Support)
- Integrate EMS strategy with broader air component objectives

You must prioritize force protection and mission success while ensuring spectrum deconfliction.""",

        "ew_planner": """ROLE: EW Planner Agent

You plan Electronic Warfare missions during Phase 3 (Weaponeering) of the ATO cycle.

Your responsibilities:
- Translate EMS strategy into specific missions
- Assign EMS assets to missions based on capability and threat
- Request frequency allocations from Spectrum Manager
- Ensure integration of EA, EP, and ES operations
- Check for EA/SIGINT fratricide
- Coordinate with strike packages

You must ensure missions are executable, properly resourced, and deconflicted.""",

        "spectrum_manager": """ROLE: Spectrum Manager Agent

You manage frequency allocation and deconfliction during Phases 3 and 5 of the ATO cycle.

Your responsibilities:
- Allocate frequencies following JCEOI (Joint Communications-Electronics Operating Instructions) process
- Deconflict spectrum usage among friendly forces
- Coordinate with other spectrum users
- Handle emergency reallocations during execution
- Maintain spectrum database

You must prevent fratricide and ensure all users have required spectrum access.""",

        "ato_producer": """ROLE: ATO Producer Agent

You integrate EMS into the Air Tasking Order during Phase 4 of the ATO cycle.

Your responsibilities:
- Collect EMS mission plans from EW Planner
- Integrate EMS with kinetic strike packages
- Generate SPINS (Special Instructions) annex for EMS
- Validate mission approvals and authorities
- Ensure ATO completeness and consistency

You must produce a coherent, executable ATO document.""",

        "assessment": """ROLE: Assessment Agent

You assess mission effectiveness during Phase 6 of the ATO cycle.

Your responsibilities:
- Collect and analyze execution data
- Assess mission effectiveness against objectives
- Analyze process improvement flags
- Generate lessons learned
- Update knowledge base with insights

You must provide actionable feedback for continuous improvement.""",
    }

    def __init__(self):
        """Initialize prompt builder."""
        pass

    def build_prompt(
        self,
        role: str,
        task_description: str,
        processed_context: ProcessedContext,
        output_schema: Optional[Dict[str, Any]] = None,
        additional_instructions: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Build complete prompt with context.

        Args:
            role: Agent role (e.g., "ems_strategy", "ew_planner")
            task_description: Specific task to perform
            processed_context: Processed context from ContextProcessor
            output_schema: Expected output schema (optional)
            additional_instructions: Additional instructions (optional)

        Returns:
            (system_prompt, user_prompt) tuple
        """
        # Build system prompt
        system_prompt = self._build_system_prompt(role)

        # Build user prompt with context
        user_prompt = self._build_user_prompt(
            task_description,
            processed_context,
            output_schema,
            additional_instructions,
        )

        logger.info(f"Built prompt for role={role}, task={task_description[:50]}...")

        return system_prompt, user_prompt

    def _build_system_prompt(self, role: str) -> str:
        """Build system prompt with role-specific instructions."""
        parts = [self.BASE_SYSTEM_PROMPT]

        # Add role-specific prompt
        if role in self.ROLE_PROMPTS:
            parts.append("\n" + self.ROLE_PROMPTS[role])
        else:
            logger.warning(f"Unknown role: {role}. Using base prompt only.")

        return "\n".join(parts)

    def _build_user_prompt(
        self,
        task_description: str,
        processed_context: ProcessedContext,
        output_schema: Optional[Dict[str, Any]],
        additional_instructions: Optional[str],
    ) -> str:
        """Build user prompt with context and task."""
        parts = []

        # Add context sections
        if processed_context.doctrinal_context:
            parts.append("=" * 80)
            parts.append("DOCTRINAL CONTEXT")
            parts.append("=" * 80)
            parts.append(processed_context.doctrinal_context)
            parts.append("")

        if processed_context.situational_context:
            parts.append("=" * 80)
            parts.append("SITUATIONAL AWARENESS")
            parts.append("=" * 80)
            parts.append(processed_context.situational_context)
            parts.append("")

        if processed_context.historical_context:
            parts.append("=" * 80)
            parts.append("HISTORICAL CONTEXT")
            parts.append("=" * 80)
            parts.append(processed_context.historical_context)
            parts.append("")

        if processed_context.collaborative_context:
            parts.append("=" * 80)
            parts.append("COLLABORATIVE CONTEXT")
            parts.append("=" * 80)
            parts.append(processed_context.collaborative_context)
            parts.append("")

        # Warning if truncated
        if processed_context.truncated:
            parts.append("⚠️  NOTE: Context was truncated to fit token budget. Work with available information.")
            parts.append("")

        # Add task
        parts.append("=" * 80)
        parts.append("YOUR TASK")
        parts.append("=" * 80)
        parts.append(task_description)
        parts.append("")

        # Add additional instructions
        if additional_instructions:
            parts.append("=" * 80)
            parts.append("ADDITIONAL INSTRUCTIONS")
            parts.append("=" * 80)
            parts.append(additional_instructions)
            parts.append("")

        # Add output requirements
        parts.append("=" * 80)
        parts.append("OUTPUT REQUIREMENTS")
        parts.append("=" * 80)

        if output_schema:
            parts.append("Provide your response as structured JSON matching this schema:")
            parts.append(f"```json")
            import json
            parts.append(json.dumps(output_schema, indent=2))
            parts.append("```")
        else:
            parts.append("Provide a clear, structured response that:")
            parts.append("1. Addresses the task completely")
            parts.append("2. Cites all context elements used (using [ID] format)")
            parts.append("3. Lists any information gaps")
            parts.append("4. Includes confidence level (0.0-1.0)")

        parts.append("")
        parts.append("Remember to cite context elements using their IDs throughout your response!")

        return "\n".join(parts)

    def build_simple_prompt(
        self,
        role: str,
        task: str,
        context_summary: str = "",
    ) -> tuple[str, str]:
        """
        Build simple prompt without full context processing.

        Useful for quick queries or when context is minimal.

        Args:
            role: Agent role
            task: Task description
            context_summary: Brief context summary

        Returns:
            (system_prompt, user_prompt) tuple
        """
        system_prompt = self._build_system_prompt(role)

        user_parts = []
        if context_summary:
            user_parts.append("CONTEXT:")
            user_parts.append(context_summary)
            user_parts.append("")

        user_parts.append("TASK:")
        user_parts.append(task)

        user_prompt = "\n".join(user_parts)

        return system_prompt, user_prompt


# Template examples for specific tasks
TASK_TEMPLATES = {
    "develop_strategy": """Develop an EMS strategy based on the following:

Mission Objectives:
{objectives}

Commander's Guidance:
{guidance}

Timeline: {timeline}

Your strategy should:
- Address all mission objectives
- Consider the threat environment
- Specify EMS effects (EA, EP, ES)
- Identify resource requirements
- Align with commander's guidance""",

    "plan_missions": """Plan EMS missions for the following operation:

Mission Type: {mission_type}
Targets: {targets}
Timeframe: {timeframe}

Your plan should:
- Assign assets to targets based on capability
- Request required frequency allocations
- Check for EA/SIGINT fratricide
- Coordinate timing with strike packages
- Ensure all targets are covered""",

    "allocate_frequencies": """Process frequency allocation requests:

Requests:
{requests}

Your allocation should:
- Follow JCEOI process
- Check for conflicts with existing allocations
- Prioritize by mission criticality
- Document any deconflictions performed
- Provide allocation details for each request""",

    "produce_ato": """Integrate EMS missions into the ATO:

EMS Mission Plans:
{mission_plans}

Strike Packages:
{strike_packages}

Your integration should:
- Align EMS with strike timing
- Generate SPINS annex
- Validate mission approvals
- Check for conflicts or gaps
- Ensure ATO completeness""",

    "assess_cycle": """Assess the effectiveness of the ATO cycle:

Execution Data:
{execution_data}

Process Improvement Flags:
{improvement_flags}

Your assessment should:
- Evaluate mission effectiveness
- Analyze process inefficiencies
- Identify patterns and trends
- Generate actionable lessons learned
- Recommend improvements""",
}


def get_task_template(task_type: str, **kwargs) -> str:
    """
    Get formatted task description from template.

    Args:
        task_type: Type of task (e.g., "develop_strategy")
        **kwargs: Values to fill template

    Returns:
        Formatted task description
    """
    if task_type not in TASK_TEMPLATES:
        logger.warning(f"Unknown task type: {task_type}")
        return kwargs.get("task_description", "")

    template = Template(TASK_TEMPLATES[task_type])
    return template.safe_substitute(**kwargs)
