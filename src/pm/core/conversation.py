"""Conversation Manager - handles LLM interactions with persona and context support."""

import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Generator, Optional

from anthropic import Anthropic

from pm.models.persona import Persona


@dataclass
class Message:
    """A conversation message."""

    role: str  # "user" or "assistant"
    content: str


@dataclass
class ConversationContext:
    """Tracks conversation state."""

    messages: list[Message] = field(default_factory=list)
    project_id: Optional[str] = None
    system_prompt: str = ""
    summary: str = ""  # Compressed context from earlier conversation

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(Message(role=role, content=content))

    def clear(self) -> None:
        """Clear conversation history."""
        self.messages = []
        self.summary = ""

    def to_api_messages(self) -> list[dict]:
        """Convert to API message format."""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def get_token_estimate(self) -> int:
        """Rough estimate of tokens in conversation (4 chars ~= 1 token)."""
        total_chars = sum(len(m.content) for m in self.messages)
        total_chars += len(self.system_prompt)
        total_chars += len(self.summary)
        return total_chars // 4


# Provider configurations
PROVIDERS = {
    "anthropic": {
        "name": "Anthropic",
        "base_url": None,  # Default Anthropic URL
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "zai": {
        "name": "z.ai",
        "base_url": "https://api.z.ai/api/anthropic",
        "api_key_env": "ZAI_API_KEY",
    },
    "minimax": {
        "name": "MiniMax",
        "base_url": "https://api.minimax.io/anthropic",
        "api_key_env": "MINIMAX_API_KEY",
    },
    "claude-cli": {
        "name": "Claude CLI",
        "base_url": None,
        "api_key_env": None,  # Uses claude CLI's own auth
        "config_dir": None,  # Default config
    },
    "claude-cli-glm": {
        "name": "Claude CLI (GLM)",
        "base_url": None,
        "api_key_env": None,
        "config_dir": "~/.glm",
    },
    "claude-cli-minimax": {
        "name": "Claude CLI (MiniMax)",
        "base_url": None,
        "api_key_env": None,
        "config_dir": "~/.minimax",
    },
}

# Available models with their configurations
AVAILABLE_MODELS = {
    # Anthropic models
    "sonnet": {
        "id": "claude-sonnet-4-20250514",
        "name": "Claude Sonnet",
        "provider": "anthropic",
        "max_tokens": 8192,
        "description": "Fast, capable model for most tasks",
    },
    "haiku": {
        "id": "claude-haiku-4-20250514",
        "name": "Claude Haiku",
        "provider": "anthropic",
        "max_tokens": 8192,
        "description": "Fastest model, good for simple tasks",
    },
    "opus": {
        "id": "claude-opus-4-20250514",
        "name": "Claude Opus",
        "provider": "anthropic",
        "max_tokens": 8192,
        "description": "Most capable model for complex reasoning",
    },
    # z.ai GLM models
    "glm-4.7": {
        "id": "glm-4.7",
        "name": "GLM-4.7",
        "provider": "zai",
        "max_tokens": 16384,
        "description": "z.ai GLM-4.7 latest model",
    },
    "glm-4.6": {
        "id": "glm-4.6",
        "name": "GLM-4.6",
        "provider": "zai",
        "max_tokens": 16384,
        "description": "z.ai GLM-4.6 general purpose model",
    },
    "glm-4.6v": {
        "id": "glm-4.6V",
        "name": "GLM-4.6V",
        "provider": "zai",
        "max_tokens": 16384,
        "description": "z.ai GLM-4.6V vision model",
    },
    # MiniMax models
    "minimax-m1": {
        "id": "MiniMax-M1",
        "name": "MiniMax M1",
        "provider": "minimax",
        "max_tokens": 16384,
        "description": "MiniMax M1 flagship model",
    },
    "minimax-m2.1": {
        "id": "MiniMax-M2.1",
        "name": "MiniMax M2.1",
        "provider": "minimax",
        "max_tokens": 16384,
        "description": "MiniMax M2.1 latest model",
    },
    # Claude CLI (uses claude command with streaming)
    "claude": {
        "id": "claude",
        "name": "Claude CLI",
        "provider": "claude-cli",
        "max_tokens": 16384,
        "description": "Claude CLI (subscription or default config)",
    },
    "claude-glm": {
        "id": "claude-glm",
        "name": "Claude CLI (GLM)",
        "provider": "claude-cli-glm",
        "max_tokens": 16384,
        "description": "Claude CLI with GLM backend (~/.glm config)",
    },
    "claude-minimax": {
        "id": "claude-minimax",
        "name": "Claude CLI (MiniMax)",
        "provider": "claude-cli-minimax",
        "max_tokens": 16384,
        "description": "Claude CLI with MiniMax backend (~/.minimax config)",
    },
}

DEFAULT_MODEL = "claude"  # Default to claude CLI


def get_provider_for_model(model_key: str) -> str:
    """Get the provider for a model key."""
    if model_key in AVAILABLE_MODELS:
        return AVAILABLE_MODELS[model_key].get("provider", "anthropic")
    return "anthropic"


class ConversationManager:
    """Manages conversations with LLM including personas and context."""

    DEFAULT_SYSTEM_PROMPT = """You are a product management assistant helping users develop their product ideas.

You help with:
- Brainstorming and refining product concepts
- Defining features and requirements
- Breaking down work into actionable tasks
- Providing multiple perspectives on design decisions

Be concise but thorough. Ask clarifying questions when requirements are ambiguous.
Focus on actionable outcomes - features, requirements, and tasks that can be executed."""

    # Token threshold for auto-summarization (roughly 50k tokens)
    SUMMARIZE_THRESHOLD = 50000

    def __init__(self, model: str = DEFAULT_MODEL):
        """Initialize conversation manager.

        Args:
            model: Model key (sonnet, haiku, opus, glm-4, etc.) or full model ID.
        """
        self._model_key = model
        self.context = ConversationContext()
        self._clients: dict[str, Anthropic] = {}  # Cache clients per provider
        self._persona: Optional[Persona] = None
        self._project_name: Optional[str] = None
        self._project_status: Optional[str] = None

    @property
    def model(self) -> str:
        """Get the full model ID."""
        if self._model_key in AVAILABLE_MODELS:
            return AVAILABLE_MODELS[self._model_key]["id"]
        return self._model_key  # Assume it's a full model ID

    @property
    def model_key(self) -> str:
        """Get the model key (sonnet, haiku, opus, etc.)."""
        return self._model_key

    @property
    def provider(self) -> str:
        """Get the current provider name."""
        return get_provider_for_model(self._model_key)

    def set_model(self, model: str) -> str:
        """Set the model to use.

        Args:
            model: Model key (sonnet, haiku, opus, glm-4, etc.) or full model ID.

        Returns:
            The model name/description.
        """
        self._model_key = model
        if model in AVAILABLE_MODELS:
            return AVAILABLE_MODELS[model]["name"]
        return model

    def _get_client(self, provider: str) -> Anthropic:
        """Get or create a client for the specified provider."""
        if provider in self._clients:
            return self._clients[provider]

        provider_config = PROVIDERS.get(provider)
        if not provider_config:
            raise ValueError(f"Unknown provider: {provider}")

        api_key_env = provider_config["api_key_env"]
        api_key = os.environ.get(api_key_env)

        if not api_key:
            # Fall back to ANTHROPIC_API_KEY for compatible providers
            api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                f"{api_key_env} environment variable is required for {provider_config['name']}. "
                f"Set it with: export {api_key_env}=your-key"
            )

        base_url = provider_config["base_url"]
        if base_url:
            client = Anthropic(api_key=api_key, base_url=base_url)
        else:
            client = Anthropic(api_key=api_key)

        self._clients[provider] = client
        return client

    @property
    def client(self) -> Anthropic:
        """Get the client for the current model's provider."""
        return self._get_client(self.provider)

    def set_persona(self, persona: Optional[Persona]) -> None:
        """Set the current persona for conversation.

        Args:
            persona: The persona to use, or None to clear.
        """
        self._persona = persona
        self._rebuild_system_prompt()

    def get_persona(self) -> Optional[Persona]:
        """Get the current persona."""
        return self._persona

    def set_project_context(self, project_id: str, project_name: str, status: str) -> None:
        """Set project-specific context."""
        self.context.project_id = project_id
        self._project_name = project_name
        self._project_status = status
        self._rebuild_system_prompt()

    def _rebuild_system_prompt(self) -> None:
        """Rebuild the system prompt based on current state."""
        parts = []

        # Base prompt
        parts.append(self.DEFAULT_SYSTEM_PROMPT)

        # Add persona if set
        if self._persona:
            parts.append("\n--- CURRENT PERSPECTIVE ---")
            parts.append(self._persona.to_system_prompt())

        # Add project context if set
        if self.context.project_id and self._project_name:
            parts.append("\n--- PROJECT CONTEXT ---")
            parts.append(f"Current project: {self._project_name} (ID: {self.context.project_id})")
            parts.append(f"Project status: {self._project_status or 'unknown'}")
            parts.append(
                "\nGuide the user through their current phase. For ideation, focus on exploring the concept. "
                "For requirements, focus on defining concrete features and requirements."
            )

        # Add conversation summary if present
        if self.context.summary:
            parts.append("\n--- CONVERSATION SUMMARY ---")
            parts.append("Earlier in this conversation:")
            parts.append(self.context.summary)

        self.context.system_prompt = "\n".join(parts)

    def chat(self, user_message: str) -> str:
        """Send a message and get a response."""
        # For non-streaming, just collect from stream
        full_response = ""
        for chunk in self.chat_stream(user_message):
            full_response += chunk
        return full_response

    def chat_stream(self, user_message: str) -> Generator[str, None, str]:
        """Send a message and stream the response.

        Yields:
            Text chunks as they arrive.

        Returns:
            The complete response text.
        """
        self.context.add_message("user", user_message)

        # Check if we should auto-summarize
        if self.context.get_token_estimate() > self.SUMMARIZE_THRESHOLD:
            self._auto_summarize()

        try:
            # Route to appropriate backend
            if self.provider.startswith("claude-cli"):
                result = yield from self._chat_stream_claude_cli(user_message)
            else:
                result = yield from self._chat_stream_api(user_message)
            return result

        except Exception as e:
            # Remove the user message if we failed
            self.context.messages.pop()
            raise RuntimeError(f"LLM request failed: {e}") from e

    def _chat_stream_api(self, user_message: str) -> Generator[str, None, str]:
        """Stream response using Anthropic API."""
        model_config = AVAILABLE_MODELS.get(self._model_key, {})
        max_tokens = model_config.get("max_tokens", 2048)

        full_response = ""

        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=self.context.system_prompt or self.DEFAULT_SYSTEM_PROMPT,
            messages=self.context.to_api_messages(),
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield text

        self.context.add_message("assistant", full_response)
        return full_response

    def _chat_stream_claude_cli(self, user_message: str) -> Generator[str, None, str]:
        """Stream response using claude CLI tool."""
        # Build the prompt with context
        system_prompt = self.context.system_prompt or self.DEFAULT_SYSTEM_PROMPT

        # Build conversation context for claude CLI
        prompt_parts = []

        # Add previous messages as context
        if len(self.context.messages) > 1:  # More than just the current message
            prompt_parts.append("Previous conversation:")
            for msg in self.context.messages[:-1]:  # Exclude current message
                role = "User" if msg.role == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg.content}")
            prompt_parts.append("")
            prompt_parts.append("Current message:")

        prompt_parts.append(user_message)
        full_prompt = "\n".join(prompt_parts)

        # Build claude CLI command
        cmd = [
            "claude",
            "-p", full_prompt,
            "--output-format", "stream-json",
            "--verbose",
        ]

        # Add system prompt
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        # Set up environment with config directory override if specified
        env = os.environ.copy()
        provider_config = PROVIDERS.get(self.provider, {})
        config_dir = provider_config.get("config_dir")
        if config_dir:
            env["CLAUDE_CONFIG_DIR"] = os.path.expanduser(config_dir)

        full_response = ""

        # Run claude CLI with streaming
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )

        try:
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # Handle different message types from claude CLI
                    if data.get("type") == "assistant":
                        # Text content from assistant
                        message = data.get("message", {})
                        content = message.get("content", [])
                        for block in content:
                            if block.get("type") == "text":
                                text = block.get("text", "")
                                if text:
                                    full_response += text
                                    yield text

                    elif data.get("type") == "content_block_delta":
                        # Streaming delta
                        delta = data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            if text:
                                full_response += text
                                yield text

                    elif data.get("type") == "result":
                        # Final result - extract text if we haven't already
                        if not full_response:
                            result_text = data.get("result", "")
                            if result_text:
                                full_response = result_text
                                yield result_text

                except json.JSONDecodeError:
                    # Not JSON, might be raw text output
                    if line and not line.startswith("{"):
                        full_response += line
                        yield line

            process.wait()

            if process.returncode != 0:
                stderr = process.stderr.read()
                raise RuntimeError(f"claude CLI failed: {stderr}")

        finally:
            process.stdout.close()
            process.stderr.close()

        self.context.add_message("assistant", full_response)
        return full_response

    def _get_summarization_client(self) -> tuple[Anthropic, str]:
        """Get client and model for summarization (prefers haiku/fast models)."""
        # Try to use a fast model for summarization
        summarize_preferences = ["haiku", "glm-4.6", "minimax-m1"]

        for model_key in summarize_preferences:
            if model_key in AVAILABLE_MODELS:
                provider = AVAILABLE_MODELS[model_key]["provider"]
                try:
                    client = self._get_client(provider)
                    return client, AVAILABLE_MODELS[model_key]["id"]
                except ValueError:
                    continue

        # Fall back to current model's client
        return self.client, self.model

    def _auto_summarize(self) -> None:
        """Automatically summarize and compress the conversation."""
        if len(self.context.messages) < 10:
            return  # Not enough to summarize

        # Keep the last 6 messages, summarize the rest
        messages_to_summarize = self.context.messages[:-6]
        messages_to_keep = self.context.messages[-6:]

        # Build summary request
        summary_content = "\n".join(
            [f"{m.role.upper()}: {m.content}" for m in messages_to_summarize]
        )

        try:
            client, model_id = self._get_summarization_client()

            response = client.messages.create(
                model=model_id,
                max_tokens=1024,
                system="You are a summarization assistant. Create a concise summary of the conversation that preserves key decisions, requirements, and context.",
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize this conversation, focusing on key decisions, requirements, and important context:\n\n{summary_content}",
                    }
                ],
            )

            new_summary = response.content[0].text

            # Combine with existing summary if present
            if self.context.summary:
                self.context.summary = f"{self.context.summary}\n\nMore recently:\n{new_summary}"
            else:
                self.context.summary = new_summary

            # Update messages to only keep recent ones
            self.context.messages = messages_to_keep

            # Rebuild prompt with new summary
            self._rebuild_system_prompt()

        except Exception:
            # Silently fail - summarization is optional
            pass

    def summarize_context(self) -> str:
        """Manually trigger context summarization.

        Returns:
            The generated summary.
        """
        if len(self.context.messages) < 4:
            return "Not enough conversation to summarize."

        # Summarize all but last 2 exchanges
        messages_to_summarize = self.context.messages[:-4]
        messages_to_keep = self.context.messages[-4:]

        if not messages_to_summarize:
            return "Not enough conversation to summarize."

        summary_content = "\n".join(
            [f"{m.role.upper()}: {m.content}" for m in messages_to_summarize]
        )

        try:
            client, model_id = self._get_summarization_client()

            response = client.messages.create(
                model=model_id,
                max_tokens=1024,
                system="You are a summarization assistant. Create a concise summary of the conversation that preserves key decisions, requirements, and context.",
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize this conversation, focusing on key decisions, requirements, and important context:\n\n{summary_content}",
                    }
                ],
            )

            new_summary = response.content[0].text

            if self.context.summary:
                self.context.summary = f"{self.context.summary}\n\nMore recently:\n{new_summary}"
            else:
                self.context.summary = new_summary

            self.context.messages = messages_to_keep
            self._rebuild_system_prompt()

            return new_summary

        except Exception as e:
            raise RuntimeError(f"Summarization failed: {e}") from e

    def clear_context(self) -> None:
        """Clear conversation history."""
        self.context.clear()
        self._rebuild_system_prompt()

    def get_context_summary(self) -> str:
        """Get a summary of the current conversation context."""
        msg_count = len(self.context.messages)
        token_estimate = self.context.get_token_estimate()

        parts = []

        if msg_count == 0:
            parts.append("No conversation history")
        else:
            parts.append(f"{msg_count} messages in conversation (~{token_estimate:,} tokens)")

        if self.context.summary:
            parts.append("Has compressed summary from earlier conversation")

        if self._persona:
            parts.append(f"Current perspective: {self._persona.name}")

        model_config = AVAILABLE_MODELS.get(self._model_key, {})
        model_name = model_config.get("name", self._model_key)
        provider_name = PROVIDERS.get(self.provider, {}).get("name", self.provider)

        if self.provider != "anthropic":
            parts.append(f"Model: {model_name} ({provider_name})")
        else:
            parts.append(f"Model: {model_name}")

        return " | ".join(parts)


def list_models_by_provider() -> dict[str, list[dict]]:
    """List all models grouped by provider."""
    result: dict[str, list[dict]] = {}

    for key, config in AVAILABLE_MODELS.items():
        provider = config.get("provider", "anthropic")
        if provider not in result:
            result[provider] = []
        result[provider].append({"key": key, **config})

    return result
