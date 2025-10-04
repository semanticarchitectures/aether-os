"""
Context-Performance Feedback Loop for Aether OS.

Uses performance data to optimize context provisioning strategies.
"""

from typing import Dict, Any, Optional
import logging

from aether_os.performance_metrics import AgentPerformanceMetrics
from aether_os.context_manager import AgentContextManager
from aether_os.performance_evaluator import AgentPerformanceEvaluator

logger = logging.getLogger(__name__)


class ContextPerformanceFeedback:
    """
    Connects context management with performance evaluation.

    Uses performance data to optimize context provisioning:
    - Low context utilization → reduce context size
    - High error rate → expand doctrinal context
    - Poor coordination → increase collaborative context
    - Missed information → expand relevant context areas
    """

    def __init__(
        self,
        context_manager: AgentContextManager,
        performance_evaluator: AgentPerformanceEvaluator,
    ):
        """
        Initialize feedback system.

        Args:
            context_manager: Context manager instance
            performance_evaluator: Performance evaluator instance
        """
        self.context_manager = context_manager
        self.performance_evaluator = performance_evaluator

        # Context strategy adjustments
        self.strategy_adjustments: Dict[str, Dict[str, Any]] = {}

        logger.info("ContextPerformanceFeedback initialized")

    def optimize_context_strategy(
        self,
        agent_id: str,
        performance_metrics: AgentPerformanceMetrics,
    ) -> Dict[str, Any]:
        """
        Adjust context strategy based on performance.

        Args:
            agent_id: Agent identifier
            performance_metrics: Latest performance metrics

        Returns:
            Dictionary of adjustments made
        """
        logger.info(f"Optimizing context strategy for {agent_id}")

        adjustments = {
            "agent_id": agent_id,
            "actions": [],
        }

        # Low context utilization → reduce size
        if performance_metrics.context_utilization < 0.5:
            logger.info(
                f"{agent_id} has low context utilization "
                f"({performance_metrics.context_utilization:.1%}), reducing context size"
            )
            adjustments["actions"].append({
                "action": "reduce_context_size",
                "reason": "low_utilization",
                "reduction_factor": 0.3,
            })

        # High context utilization but low output quality → need better context
        if performance_metrics.context_utilization > 0.8 and performance_metrics.output_quality_score < 0.7:
            logger.info(
                f"{agent_id} using context heavily but low output quality, "
                "improving context quality"
            )
            adjustments["actions"].append({
                "action": "improve_context_quality",
                "reason": "high_use_low_quality",
            })

        # High error rate → expand doctrinal context
        if performance_metrics.error_rate > 0.1:
            logger.info(
                f"{agent_id} has high error rate ({performance_metrics.error_rate:.1%}), "
                "expanding doctrinal context"
            )
            adjustments["actions"].append({
                "action": "expand_doctrinal_context",
                "reason": "high_error_rate",
                "expansion_factor": 0.3,
            })

        # Poor coordination → increase collaborative context
        if performance_metrics.coordination_effectiveness < 0.7:
            logger.info(
                f"{agent_id} has poor coordination "
                f"({performance_metrics.coordination_effectiveness:.2f}), "
                "expanding collaborative context"
            )
            adjustments["actions"].append({
                "action": "expand_collaborative_context",
                "reason": "poor_coordination",
                "expansion_factor": 0.2,
            })

        # Low mission success → expand situational awareness
        if performance_metrics.mission_success_rate < 0.8:
            logger.info(
                f"{agent_id} has low success rate "
                f"({performance_metrics.mission_success_rate:.1%}), "
                "expanding situational context"
            )
            adjustments["actions"].append({
                "action": "expand_situational_context",
                "reason": "low_success_rate",
                "expansion_factor": 0.3,
            })

        # Slow response time → add priority caching
        if performance_metrics.inter_agent_response_time > 10.0:
            logger.info(
                f"{agent_id} has slow response time "
                f"({performance_metrics.inter_agent_response_time:.1f} min), "
                "adding priority caching"
            )
            adjustments["actions"].append({
                "action": "enable_priority_caching",
                "reason": "slow_response_time",
            })

        # Good performance → use as template
        if performance_metrics.overall_score > 0.85:
            logger.info(
                f"{agent_id} has excellent performance "
                f"({performance_metrics.overall_score:.2f}), "
                "marking as template"
            )
            adjustments["actions"].append({
                "action": "mark_as_template",
                "reason": "excellent_performance",
            })

        # Store adjustments
        self.strategy_adjustments[agent_id] = adjustments

        logger.info(
            f"Context strategy optimization complete: {len(adjustments['actions'])} adjustments"
        )

        return adjustments

    def apply_adjustments(
        self,
        agent_id: str,
        orchestrator: Any = None,
    ):
        """
        Apply stored adjustments to context manager.

        Args:
            agent_id: Agent to apply adjustments for
            orchestrator: Orchestrator for current cycle info
        """
        adjustments = self.strategy_adjustments.get(agent_id)

        if not adjustments:
            logger.debug(f"No adjustments to apply for {agent_id}")
            return

        logger.info(f"Applying {len(adjustments['actions'])} adjustments for {agent_id}")

        for action_item in adjustments["actions"]:
            action = action_item["action"]
            reason = action_item["reason"]

            logger.debug(f"Applying {action} (reason: {reason})")

            # In production, would actually modify context manager parameters
            # For prototype, just log the actions

        logger.info(f"Adjustments applied for {agent_id}")

    def generate_optimization_report(self) -> str:
        """Generate report of optimization actions taken."""
        if not self.strategy_adjustments:
            return "No context strategy optimizations performed yet."

        report = "=" * 60 + "\n"
        report += "CONTEXT STRATEGY OPTIMIZATION REPORT\n"
        report += "=" * 60 + "\n\n"

        for agent_id, adjustments in self.strategy_adjustments.items():
            report += f"Agent: {agent_id}\n"
            report += f"Adjustments: {len(adjustments['actions'])}\n"

            for action in adjustments["actions"]:
                report += f"  - {action['action']} (reason: {action['reason']})\n"

            report += "\n"

        return report

    def analyze_context_performance_correlation(self) -> Dict[str, Any]:
        """
        Analyze correlation between context strategies and performance.

        Returns:
            Analysis of what context strategies work best
        """
        analysis = {
            "high_performers": [],
            "low_performers": [],
            "recommendations": [],
        }

        # Get performance data
        for agent_id, history in self.performance_evaluator.performance_history.items():
            if not history:
                continue

            latest = history[-1]

            if latest.overall_score > 0.8:
                # Get context stats
                context_stats = self.context_manager.get_context_statistics(agent_id)

                analysis["high_performers"].append({
                    "agent_id": agent_id,
                    "overall_score": latest.overall_score,
                    "context_utilization": latest.context_utilization,
                    "avg_context_size": context_stats.get("avg_context_size", 0),
                })

            elif latest.overall_score < 0.6:
                context_stats = self.context_manager.get_context_statistics(agent_id)

                analysis["low_performers"].append({
                    "agent_id": agent_id,
                    "overall_score": latest.overall_score,
                    "context_utilization": latest.context_utilization,
                    "avg_context_size": context_stats.get("avg_context_size", 0),
                })

        # Generate recommendations
        if analysis["high_performers"]:
            avg_high_util = sum(
                p["context_utilization"] for p in analysis["high_performers"]
            ) / len(analysis["high_performers"])

            analysis["recommendations"].append(
                f"High performers average {avg_high_util:.1%} context utilization"
            )

        if analysis["low_performers"]:
            for performer in analysis["low_performers"]:
                if performer["context_utilization"] < 0.4:
                    analysis["recommendations"].append(
                        f"{performer['agent_id']}: Reduce context size (low utilization)"
                    )
                elif performer["context_utilization"] > 0.8:
                    analysis["recommendations"].append(
                        f"{performer['agent_id']}: Improve context quality (high use, low output)"
                    )

        return analysis
