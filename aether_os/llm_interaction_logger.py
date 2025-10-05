"""
LLM Interaction Logger for Aether OS.

Provides detailed logging of all LLM prompts and responses for debugging,
analysis, and audit purposes.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMInteractionLogger:
    """
    Logs detailed LLM interactions to dedicated files.
    
    Creates separate log files for:
    - Full prompts and responses (llm_interactions.log)
    - Structured JSON data (llm_interactions.jsonl)
    """
    
    def __init__(self, log_dir: str = "."):
        """
        Initialize LLM interaction logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Set up file paths
        self.text_log_path = self.log_dir / "llm_interactions.log"
        self.json_log_path = self.log_dir / "llm_interactions.jsonl"
        
        # Initialize log files if they don't exist
        self._initialize_log_files()
        
        logger.info(f"LLM interaction logger initialized: {self.log_dir}")
    
    def _initialize_log_files(self):
        """Initialize log files with headers."""
        if not self.text_log_path.exists():
            with open(self.text_log_path, 'w') as f:
                f.write("# Aether OS LLM Interaction Log\n")
                f.write(f"# Started: {datetime.now().isoformat()}\n")
                f.write("# Format: Timestamp | Agent | Provider | Model | Tokens | Status\n")
                f.write("#" + "="*80 + "\n\n")
        
        if not self.json_log_path.exists():
            with open(self.json_log_path, 'w') as f:
                # JSONL format - one JSON object per line
                pass
    
    def log_interaction(
        self,
        agent_id: str,
        provider: str,
        model: str,
        system_prompt: Optional[str],
        user_prompt: str,
        response_content: str,
        tokens_used: int,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a complete LLM interaction.
        
        Args:
            agent_id: ID of the agent making the request
            provider: LLM provider (anthropic, openai, google)
            model: Model name used
            system_prompt: System prompt sent
            user_prompt: User prompt sent
            response_content: Response received
            tokens_used: Number of tokens consumed
            success: Whether the interaction succeeded
            error: Error message if failed
            metadata: Additional metadata
        """
        timestamp = datetime.now()
        
        # Log to text file
        self._log_to_text_file(
            timestamp, agent_id, provider, model, system_prompt, 
            user_prompt, response_content, tokens_used, success, error
        )
        
        # Log to JSON file
        self._log_to_json_file(
            timestamp, agent_id, provider, model, system_prompt,
            user_prompt, response_content, tokens_used, success, error, metadata
        )
    
    def _log_to_text_file(
        self,
        timestamp: datetime,
        agent_id: str,
        provider: str,
        model: str,
        system_prompt: Optional[str],
        user_prompt: str,
        response_content: str,
        tokens_used: int,
        success: bool,
        error: Optional[str]
    ):
        """Log interaction to human-readable text file."""
        status = "SUCCESS" if success else "FAILED"
        
        with open(self.text_log_path, 'a') as f:
            f.write(f"[{timestamp.isoformat()}] {agent_id} | {provider} | {model} | {tokens_used} tokens | {status}\n")
            f.write("=" * 100 + "\n")
            
            if system_prompt:
                f.write("SYSTEM PROMPT:\n")
                f.write("-" * 50 + "\n")
                f.write(system_prompt + "\n\n")
            
            f.write("USER PROMPT:\n")
            f.write("-" * 50 + "\n")
            f.write(user_prompt + "\n\n")
            
            if success:
                f.write("RESPONSE:\n")
                f.write("-" * 50 + "\n")
                f.write(response_content + "\n\n")
            else:
                f.write("ERROR:\n")
                f.write("-" * 50 + "\n")
                f.write(str(error) + "\n\n")
            
            f.write("=" * 100 + "\n\n")
    
    def _log_to_json_file(
        self,
        timestamp: datetime,
        agent_id: str,
        provider: str,
        model: str,
        system_prompt: Optional[str],
        user_prompt: str,
        response_content: str,
        tokens_used: int,
        success: bool,
        error: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ):
        """Log interaction to structured JSON Lines file."""
        interaction_data = {
            "timestamp": timestamp.isoformat(),
            "agent_id": agent_id,
            "provider": provider,
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response_content": response_content if success else None,
            "tokens_used": tokens_used,
            "success": success,
            "error": error,
            "metadata": metadata or {},
            "system_prompt_length": len(system_prompt) if system_prompt else 0,
            "user_prompt_length": len(user_prompt),
            "response_length": len(response_content) if success else 0
        }
        
        with open(self.json_log_path, 'a') as f:
            f.write(json.dumps(interaction_data) + "\n")
    
    def get_interaction_stats(self) -> Dict[str, Any]:
        """
        Get statistics about logged interactions.
        
        Returns:
            Dictionary with interaction statistics
        """
        if not self.json_log_path.exists():
            return {"total_interactions": 0}
        
        stats = {
            "total_interactions": 0,
            "successful_interactions": 0,
            "failed_interactions": 0,
            "total_tokens": 0,
            "providers": {},
            "agents": {},
            "models": {}
        }
        
        try:
            with open(self.json_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        stats["total_interactions"] += 1
                        
                        if data["success"]:
                            stats["successful_interactions"] += 1
                        else:
                            stats["failed_interactions"] += 1
                        
                        stats["total_tokens"] += data.get("tokens_used", 0)
                        
                        # Count by provider
                        provider = data["provider"]
                        stats["providers"][provider] = stats["providers"].get(provider, 0) + 1
                        
                        # Count by agent
                        agent = data["agent_id"]
                        stats["agents"][agent] = stats["agents"].get(agent, 0) + 1
                        
                        # Count by model
                        model = data["model"]
                        stats["models"][model] = stats["models"].get(model, 0) + 1
        
        except Exception as e:
            logger.warning(f"Error reading interaction stats: {e}")
        
        return stats
    
    def search_interactions(
        self,
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        success_only: bool = False,
        limit: int = 10
    ) -> list:
        """
        Search logged interactions by criteria.
        
        Args:
            agent_id: Filter by agent ID
            provider: Filter by provider
            success_only: Only return successful interactions
            limit: Maximum number of results
            
        Returns:
            List of matching interactions
        """
        if not self.json_log_path.exists():
            return []
        
        results = []
        
        try:
            with open(self.json_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        
                        # Apply filters
                        if agent_id and data["agent_id"] != agent_id:
                            continue
                        if provider and data["provider"] != provider:
                            continue
                        if success_only and not data["success"]:
                            continue
                        
                        results.append(data)
                        
                        if len(results) >= limit:
                            break
        
        except Exception as e:
            logger.warning(f"Error searching interactions: {e}")
        
        return results


# Global instance
_llm_logger = None


def get_llm_logger() -> LLMInteractionLogger:
    """Get the global LLM interaction logger instance."""
    global _llm_logger
    if _llm_logger is None:
        _llm_logger = LLMInteractionLogger()
    return _llm_logger


def log_llm_interaction(
    agent_id: str,
    provider: str,
    model: str,
    system_prompt: Optional[str],
    user_prompt: str,
    response_content: str,
    tokens_used: int,
    success: bool,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Convenience function to log an LLM interaction.
    
    Uses the global logger instance.
    """
    logger_instance = get_llm_logger()
    logger_instance.log_interaction(
        agent_id, provider, model, system_prompt, user_prompt,
        response_content, tokens_used, success, error, metadata
    )
