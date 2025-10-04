"""
Evaluator Agent for Aether OS Agent Testing.

Special agent that evaluates other agents' responses based on
quality criteria, doctrinal compliance, and task completion.
"""

from typing import Dict, Any, List, Optional
import logging
import os

from agents.base_agent import BaseAetherAgent

# LLM integration
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class EvaluatorAgent(BaseAetherAgent):
    """
    Evaluator Agent - Assesses other agents' performance.

    This agent reviews agent responses and provides:
    - Quality scores
    - Criterion-based evaluation
    - Feedback and recommendations
    - Pass/fail determination
    """

    def __init__(self, aether_os: Any):
        """Initialize Evaluator Agent."""
        super().__init__(agent_id="evaluator_agent", aether_os=aether_os)

        # Initialize LLM client if available
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.llm_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            self.llm_client = None
            logger.warning("Anthropic API not available - using rule-based evaluation")

    async def execute_phase_tasks(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """Evaluator agent is not phase-specific."""
        logger.info(f"[{self.agent_id}] Evaluator agent is not tied to ATO phases")
        return {}

    def evaluate_agent_responses(
        self,
        evaluation_request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate agent responses against criteria.

        Args:
            evaluation_request: Dictionary containing:
                - scenario_name: Name of test scenario
                - scenario_description: Description
                - evaluation_criteria: Criteria to evaluate against
                - responses: List of agent responses
                - context_provided: Context given to agent
                - context_utilization: How much context was used

        Returns:
            Evaluation results with scores and feedback
        """
        logger.info(
            f"[{self.agent_id}] Evaluating agent responses for scenario: "
            f"{evaluation_request.get('scenario_name')}"
        )

        scenario_name = evaluation_request.get("scenario_name", "Unknown")
        scenario_desc = evaluation_request.get("scenario_description", "")
        criteria = evaluation_request.get("evaluation_criteria", {})
        responses = evaluation_request.get("responses", [])
        context_util = evaluation_request.get("context_utilization", 0.0)

        # Use LLM evaluation if available, otherwise rule-based
        if self.llm_client:
            return self._evaluate_with_llm(
                scenario_name, scenario_desc, criteria, responses, context_util
            )
        else:
            return self._evaluate_rule_based(
                scenario_name, scenario_desc, criteria, responses, context_util
            )

    def _evaluate_with_llm(
        self,
        scenario_name: str,
        scenario_desc: str,
        criteria: Dict[str, Any],
        responses: List[Dict[str, Any]],
        context_util: float,
    ) -> Dict[str, Any]:
        """Use LLM to evaluate responses."""
        logger.info(f"[{self.agent_id}] Using LLM-based evaluation")

        # Prepare evaluation prompt
        prompt = self._build_evaluation_prompt(
            scenario_name, scenario_desc, criteria, responses, context_util
        )

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            evaluation_text = response.content[0].text

            # Parse LLM response (simplified - would use structured output in production)
            evaluation = self._parse_llm_evaluation(evaluation_text, criteria)

            logger.info(
                f"[{self.agent_id}] LLM evaluation complete: "
                f"Score {evaluation['overall_score']:.2f}"
            )

            return evaluation

        except Exception as e:
            logger.error(f"Error in LLM evaluation: {e}", exc_info=True)
            return self._evaluate_rule_based(
                scenario_name, scenario_desc, criteria, responses, context_util
            )

    def _build_evaluation_prompt(
        self,
        scenario_name: str,
        scenario_desc: str,
        criteria: Dict[str, Any],
        responses: List[Dict[str, Any]],
        context_util: float,
    ) -> str:
        """Build prompt for LLM evaluation."""
        prompt = f"""You are an expert evaluator assessing an AI agent's performance.

**Scenario**: {scenario_name}
{scenario_desc}

**Evaluation Criteria**:
"""
        for criterion, details in criteria.items():
            weight = details.get("weight", 1.0) if isinstance(details, dict) else 1.0
            prompt += f"- {criterion} (weight: {weight})\n"

        prompt += f"""
**Agent Responses**:
"""
        for idx, response in enumerate(responses):
            prompt += f"\nMessage {idx + 1}:\n"
            prompt += f"Type: {response.get('message_type')}\n"
            prompt += f"Response: {response.get('response')}\n"

        prompt += f"""
**Context Utilization**: {context_util:.1%}

Please evaluate the agent's performance:
1. Score each criterion from 0.0 to 1.0
2. Calculate an overall score (weighted average)
3. Determine if the agent PASSED or FAILED (pass threshold: 0.7)
4. Provide brief feedback on strengths and weaknesses

Format your response as:
CRITERION SCORES:
[criterion]: [score]
...

OVERALL SCORE: [score]

RESULT: PASS/FAIL

FEEDBACK:
[Your feedback here]
"""
        return prompt

    def _parse_llm_evaluation(
        self,
        evaluation_text: str,
        criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Parse LLM evaluation response."""
        # Simplified parsing - extract scores and feedback
        lines = evaluation_text.split("\n")

        criteria_scores = {}
        overall_score = 0.5
        passed = False
        feedback = evaluation_text

        # Try to extract scores
        for line in lines:
            # Look for criterion scores
            for criterion in criteria.keys():
                if criterion.lower() in line.lower() and ":" in line:
                    try:
                        score_str = line.split(":")[-1].strip()
                        score = float(score_str)
                        criteria_scores[criterion] = min(max(score, 0.0), 1.0)
                    except:
                        pass

            # Look for overall score
            if "overall score" in line.lower() and ":" in line:
                try:
                    score_str = line.split(":")[-1].strip()
                    overall_score = float(score_str)
                except:
                    pass

            # Look for pass/fail
            if "result" in line.lower():
                passed = "pass" in line.lower() and "fail" not in line.lower()

        # Extract feedback section
        if "FEEDBACK:" in evaluation_text:
            feedback = evaluation_text.split("FEEDBACK:")[-1].strip()

        return {
            "overall_score": overall_score,
            "criteria_scores": criteria_scores,
            "passed": passed,
            "feedback": feedback,
            "raw_evaluation": evaluation_text,
        }

    def _evaluate_rule_based(
        self,
        scenario_name: str,
        scenario_desc: str,
        criteria: Dict[str, Any],
        responses: List[Dict[str, Any]],
        context_util: float,
    ) -> Dict[str, Any]:
        """Rule-based evaluation without LLM."""
        logger.info(f"[{self.agent_id}] Using rule-based evaluation")

        criteria_scores = {}
        feedback_items = []

        # Evaluate each criterion
        for criterion_name, criterion_config in criteria.items():
            if isinstance(criterion_config, dict):
                criterion_type = criterion_config.get("type", "quality")
                target = criterion_config.get("target", 0.7)
            else:
                criterion_type = "quality"
                target = 0.7

            score = self._evaluate_criterion(
                criterion_name, criterion_type, responses, context_util
            )

            criteria_scores[criterion_name] = score

            # Generate feedback
            if score >= target:
                feedback_items.append(
                    f"✓ {criterion_name}: Meets expectations ({score:.2f})"
                )
            else:
                feedback_items.append(
                    f"✗ {criterion_name}: Below target ({score:.2f} vs {target:.2f})"
                )

        # Calculate overall score
        if criteria:
            weights = {
                k: (v.get("weight", 1.0) if isinstance(v, dict) else 1.0)
                for k, v in criteria.items()
            }
            total_weight = sum(weights.values())
            overall_score = sum(
                criteria_scores.get(k, 0.0) * weights[k]
                for k in criteria.keys()
            ) / total_weight if total_weight > 0 else 0.0
        else:
            # Default: success rate
            overall_score = sum(
                1 for r in responses if r.get("response", {}).get("success")
            ) / len(responses) if responses else 0.0

        # Determine pass/fail
        pass_threshold = 0.7
        passed = overall_score >= pass_threshold

        feedback = "\n".join(feedback_items)
        if not passed:
            feedback += f"\n\nOverall score {overall_score:.2f} is below pass threshold {pass_threshold:.2f}"

        return {
            "overall_score": overall_score,
            "criteria_scores": criteria_scores,
            "passed": passed,
            "feedback": feedback,
        }

    def _evaluate_criterion(
        self,
        criterion_name: str,
        criterion_type: str,
        responses: List[Dict[str, Any]],
        context_util: float,
    ) -> float:
        """Evaluate a single criterion."""
        criterion_lower = criterion_name.lower()

        # Success rate criterion
        if "success" in criterion_lower or "completion" in criterion_lower:
            if not responses:
                return 0.0
            successful = sum(
                1 for r in responses if r.get("response", {}).get("success")
            )
            return successful / len(responses)

        # Response time criterion
        elif "time" in criterion_lower or "speed" in criterion_lower:
            # Default good score for rule-based
            return 0.8

        # Context utilization criterion
        elif "context" in criterion_lower or "utilization" in criterion_lower:
            return context_util

        # Doctrinal compliance criterion
        elif "doctrine" in criterion_lower or "compliance" in criterion_lower:
            # Check if responses mention doctrine/procedures
            mentions = sum(
                1 for r in responses
                if "doctrine" in str(r.get("response", {})).lower()
                or "procedure" in str(r.get("response", {})).lower()
            )
            return min(mentions / len(responses), 1.0) if responses else 0.5

        # Quality criterion (default)
        else:
            # Default quality score based on response completeness
            if not responses:
                return 0.0

            quality_scores = []
            for response in responses:
                resp_data = response.get("response", {})

                # Check if response has data
                if resp_data.get("success") and resp_data.get("data"):
                    quality_scores.append(1.0)
                elif resp_data.get("success"):
                    quality_scores.append(0.7)
                else:
                    quality_scores.append(0.3)

            return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
