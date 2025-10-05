"""
LLM Client for Aether OS.

Multi-provider LLM client with retry logic, rate limiting,
and structured output parsing.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

from .llm_interaction_logger import log_llm_interaction

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


@dataclass
class LLMResponse:
    """Structured LLM response."""
    content: str
    model: str
    provider: LLMProvider
    tokens_used: int
    finish_reason: str
    raw_response: Any = None


class LLMClient:
    """
    Multi-provider LLM client with automatic fallback.

    Supports:
    - Anthropic Claude (primary)
    - OpenAI GPT-4 (fallback)
    - Google Gemini (fallback)
    """

    def __init__(
        self,
        primary_provider: LLMProvider = LLMProvider.ANTHROPIC,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 60.0,
    ):
        """
        Initialize LLM client.

        Args:
            primary_provider: Primary LLM provider to use
            max_retries: Maximum retry attempts per provider
            retry_delay: Delay between retries (seconds)
            timeout: Request timeout (seconds)
        """
        self.primary_provider = primary_provider
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        # Initialize clients
        self._init_clients()

    def _init_clients(self):
        """Initialize available LLM provider clients."""
        self.clients = {}

        # Anthropic Claude
        try:
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.clients[LLMProvider.ANTHROPIC] = Anthropic(api_key=api_key)
                logger.info("Anthropic client initialized")
        except ImportError:
            logger.warning("Anthropic library not available")

        # OpenAI GPT
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.clients[LLMProvider.OPENAI] = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
        except ImportError:
            logger.warning("OpenAI library not available")

        # Google Gemini
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.clients[LLMProvider.GOOGLE] = genai
                logger.info("Google Gemini client initialized")
        except ImportError:
            logger.warning("Google Gemini library not available")

        if not self.clients:
            logger.error("No LLM providers available")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.3,
        model: Optional[str] = None,
        structured_output: Optional[type] = None,
    ) -> LLMResponse:
        """
        Generate response from LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model: Specific model to use (optional)
            structured_output: Pydantic model for structured output

        Returns:
            LLMResponse with generated content

        Raises:
            RuntimeError: If all providers fail
        """
        # Try primary provider first
        providers = [self.primary_provider]

        # Add fallback providers
        for provider in LLMProvider:
            if provider != self.primary_provider and provider in self.clients:
                providers.append(provider)

        last_error = None

        for provider in providers:
            if provider not in self.clients:
                continue

            logger.info(f"Attempting generation with {provider.value}")

            # Log the prompt being sent (debug level for full content)
            logger.debug(f"System prompt ({len(system_prompt or '')} chars): {(system_prompt or '')[:200]}...")
            logger.debug(f"User prompt ({len(prompt)} chars): {prompt[:200]}...")

            try:
                response = self._generate_with_provider(
                    provider=provider,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=model,
                    structured_output=structured_output,
                )

                # Log the response content (debug level for full content)
                logger.info(f"Successfully generated response with {provider.value}")
                logger.debug(f"Response content ({len(response.content)} chars): {response.content[:200]}...")
                logger.info(f"Token usage: {response.tokens_used} tokens")

                # Log full interaction to dedicated LLM log
                log_llm_interaction(
                    agent_id=getattr(self, '_current_agent_id', 'unknown'),
                    provider=provider.value,
                    model=response.model,
                    system_prompt=system_prompt,
                    user_prompt=prompt,
                    response_content=response.content,
                    tokens_used=response.tokens_used,
                    success=True,
                    metadata={
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "structured_output": structured_output is not None
                    }
                )

                return response

            except Exception as e:
                logger.warning(f"Failed with {provider.value}: {e}")

                # Log failed interaction
                log_llm_interaction(
                    agent_id=getattr(self, '_current_agent_id', 'unknown'),
                    provider=provider.value,
                    model=model or "default",
                    system_prompt=system_prompt,
                    user_prompt=prompt,
                    response_content="",
                    tokens_used=0,
                    success=False,
                    error=str(e),
                    metadata={
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "structured_output": structured_output is not None
                    }
                )

                last_error = e
                continue

        # All providers failed
        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    def _generate_with_provider(
        self,
        provider: LLMProvider,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        model: Optional[str],
        structured_output: Optional[type],
    ) -> LLMResponse:
        """Generate response with specific provider."""

        if provider == LLMProvider.ANTHROPIC:
            return self._generate_anthropic(
                prompt, system_prompt, max_tokens, temperature, model, structured_output
            )
        elif provider == LLMProvider.OPENAI:
            return self._generate_openai(
                prompt, system_prompt, max_tokens, temperature, model, structured_output
            )
        elif provider == LLMProvider.GOOGLE:
            return self._generate_google(
                prompt, system_prompt, max_tokens, temperature, model, structured_output
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        model: Optional[str],
        structured_output: Optional[type],
    ) -> LLMResponse:
        """Generate with Anthropic Claude."""
        client = self.clients[LLMProvider.ANTHROPIC]

        # Default model
        if not model:
            model = "claude-sonnet-4-20250514"

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Make request with retry
        for attempt in range(self.max_retries):
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt if system_prompt else "",
                    messages=messages,
                )

                content = response.content[0].text

                # Parse structured output if requested
                if structured_output:
                    import json
                    import re

                    # Clean up content - remove markdown code blocks if present
                    cleaned_content = content.strip()
                    if cleaned_content.startswith('```json'):
                        # Extract JSON from markdown code block
                        json_match = re.search(r'```json\s*\n(.*?)\n```', cleaned_content, re.DOTALL)
                        if json_match:
                            cleaned_content = json_match.group(1).strip()
                    elif cleaned_content.startswith('```'):
                        # Extract from generic code block
                        json_match = re.search(r'```\s*\n(.*?)\n```', cleaned_content, re.DOTALL)
                        if json_match:
                            cleaned_content = json_match.group(1).strip()

                    # Try to parse and validate
                    try:
                        parsed = structured_output.model_validate_json(cleaned_content)
                        content = parsed.model_dump_json()
                    except Exception as parse_error:
                        logger.warning(f"Failed to parse structured output: {parse_error}")
                        logger.warning(f"Raw content: {content[:200]}...")
                        # Try to extract JSON from the content if it's mixed with text
                        json_match = re.search(r'\{.*\}', cleaned_content, re.DOTALL)
                        if json_match:
                            try:
                                parsed = structured_output.model_validate_json(json_match.group(0))
                                content = parsed.model_dump_json()
                            except:
                                raise parse_error
                        else:
                            raise parse_error

                return LLMResponse(
                    content=content,
                    model=model,
                    provider=LLMProvider.ANTHROPIC,
                    tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                    finish_reason=response.stop_reason,
                    raw_response=response,
                )

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Anthropic attempt {attempt + 1} failed: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise

    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        model: Optional[str],
        structured_output: Optional[type],
    ) -> LLMResponse:
        """Generate with OpenAI GPT."""
        client = self.clients[LLMProvider.OPENAI]

        # Default model
        if not model:
            model = "gpt-4o"

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Make request with retry
        for attempt in range(self.max_retries):
            try:
                if structured_output:
                    # Use regular completion with JSON mode for better compatibility
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        response_format={"type": "json_object"},
                    )
                    content = response.choices[0].message.content

                    # Parse and validate the JSON response
                    import json
                    try:
                        json_data = json.loads(content)
                        parsed = structured_output.model_validate(json_data)
                        content = parsed.model_dump_json()
                    except Exception as parse_error:
                        logger.warning(f"Failed to parse OpenAI structured output: {parse_error}")
                        logger.warning(f"Raw content: {content[:200]}...")
                        raise parse_error
                else:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    content = response.choices[0].message.content

                return LLMResponse(
                    content=content,
                    model=model,
                    provider=LLMProvider.OPENAI,
                    tokens_used=response.usage.total_tokens,
                    finish_reason=response.choices[0].finish_reason,
                    raw_response=response,
                )

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"OpenAI attempt {attempt + 1} failed: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise

    def _generate_google(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        model: Optional[str],
        structured_output: Optional[type],
    ) -> LLMResponse:
        """Generate with Google Gemini."""
        genai = self.clients[LLMProvider.GOOGLE]

        # Default model
        if not model:
            model = "gemini-pro"

        # Combine system and user prompt for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Make request with retry
        for attempt in range(self.max_retries):
            try:
                model_instance = genai.GenerativeModel(model)

                response = model_instance.generate_content(
                    full_prompt,
                    generation_config={
                        "max_output_tokens": max_tokens,
                        "temperature": temperature,
                    }
                )

                content = response.text

                # Parse structured output if requested
                if structured_output:
                    import json
                    import re

                    # Clean up content - remove markdown code blocks if present
                    cleaned_content = content.strip()
                    if cleaned_content.startswith('```json'):
                        # Extract JSON from markdown code block
                        json_match = re.search(r'```json\s*\n(.*?)\n```', cleaned_content, re.DOTALL)
                        if json_match:
                            cleaned_content = json_match.group(1).strip()
                    elif cleaned_content.startswith('```'):
                        # Extract from generic code block
                        json_match = re.search(r'```\s*\n(.*?)\n```', cleaned_content, re.DOTALL)
                        if json_match:
                            cleaned_content = json_match.group(1).strip()

                    # Try to parse and validate
                    try:
                        parsed = structured_output.model_validate_json(cleaned_content)
                        content = parsed.model_dump_json()
                    except Exception as parse_error:
                        logger.warning(f"Failed to parse Google structured output: {parse_error}")
                        logger.warning(f"Raw content: {content[:200]}...")
                        # Try to extract JSON from the content if it's mixed with text
                        json_match = re.search(r'\{.*\}', cleaned_content, re.DOTALL)
                        if json_match:
                            try:
                                parsed = structured_output.model_validate_json(json_match.group(0))
                                content = parsed.model_dump_json()
                            except:
                                raise parse_error
                        else:
                            raise parse_error

                return LLMResponse(
                    content=content,
                    model=model,
                    provider=LLMProvider.GOOGLE,
                    tokens_used=response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
                    finish_reason="stop",
                    raw_response=response,
                )

            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Google attempt {attempt + 1} failed: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise

    def is_available(self) -> bool:
        """Check if any LLM provider is available."""
        return len(self.clients) > 0

    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers."""
        return list(self.clients.keys())
