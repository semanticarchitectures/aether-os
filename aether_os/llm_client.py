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
                logger.info(f"Successfully generated response with {provider.value}")
                return response

            except Exception as e:
                logger.warning(f"Failed with {provider.value}: {e}")
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
                    parsed = structured_output.model_validate_json(content)
                    content = parsed.model_dump_json()

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
                    response = client.beta.chat.completions.parse(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        response_format=structured_output,
                    )
                    content = response.choices[0].message.parsed.model_dump_json()
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
            model = "gemini-1.5-pro"

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
                    parsed = structured_output.model_validate_json(content)
                    content = parsed.model_dump_json()

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
