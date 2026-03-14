import autogen
from backend.config import get_llm_config
from backend.utils.logger import get_logger
from datetime import datetime, date
from typing import Any, Dict
import json
import re
import asyncio

logger = get_logger(__name__)

# Groq free tier hard limit is 6000 TPM.
_MAX_DATA_CHARS = 3000


class _SafeEncoder(json.JSONEncoder):
    """JSON encoder that handles pandas Timestamps, dates, and other non-serializable types."""
    def default(self, obj):
        if hasattr(obj, 'isoformat'):  # datetime, date, pd.Timestamp
            return obj.isoformat()
        if hasattr(obj, 'item'):       # numpy scalars
            return obj.item()
        if hasattr(obj, 'tolist'):     # numpy arrays
            return obj.tolist()
        return str(obj)


def safe_json_dumps(data: Any) -> str:
    """Serialize to JSON, safely handling pandas Timestamps and numpy types."""
    return json.dumps(data, cls=_SafeEncoder)


class BaseAgent:
    """Base class for all BI agents"""

    def __init__(self, name: str):
        self.name = name
        llm_config = {
            "config_list": get_llm_config(),
            "cache_seed": None,
        }
        self.autogen_agent = autogen.ConversableAgent(
            name=name,
            llm_config=llm_config,
            human_input_mode="NEVER",
        )

    async def llm_call(self, prompt: str, retries: int = 3) -> str:
        """Make LLM call with automatic retry on 429 rate-limit errors."""
        for attempt in range(retries):
            try:
                response = await self.autogen_agent.a_generate_reply(
                    messages=[{"content": prompt, "role": "user"}]
                )
                return str(response)
            except Exception as e:
                err = str(e)
                # Groq returns the retry delay in the error message — parse and use it
                if "rate_limit_exceeded" in err or "429" in err:
                    wait = 5.0
                    match = re.search(r'try again in ([\d.]+)s', err)
                    if match:
                        wait = float(match.group(1)) + 0.5
                    if attempt < retries - 1:
                        logger.warning(f"Rate limit hit, retrying in {wait:.1f}s (attempt {attempt+1}/{retries})")
                        await asyncio.sleep(wait)
                        continue
                logger.error(f"LLM call failed: {e}")
                return f"Error generating response: {str(e)}"
        return "Error generating response: max retries exceeded"

    async def llm_json_call(self, prompt: str) -> Any:
        """
        LLM call that parses and returns the response as a Python object.
        Strips markdown code fences, falls back to empty dict on parse failure.
        """
        raw = await self.llm_call(prompt)
        clean = re.sub(r"```json|```", "", raw).strip()
        try:
            return json.loads(clean)
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"Could not parse LLM JSON response: {clean[:200]}")
            return {}

    def _truncate(self, data: Any, max_chars: int = _MAX_DATA_CHARS) -> str:
        """
        Safely serialize any object to a string and truncate it to max_chars.
        Prevents 413 token-limit errors on Groq free tier.
        """
        if isinstance(data, str):
            text = data
        else:
            try:
                text = json.dumps(data, default=str)
            except Exception:
                text = str(data)

        if len(text) > max_chars:
            text = text[:max_chars] + "... [truncated]"
        return text

    def _get_timestamp(self) -> str:
        return datetime.now().isoformat()


def create_agent(
    name: str,
    system_message: str,
    tools: list = None
) -> autogen.ConversableAgent:
    """Factory function to create AutoGen agents configured for Groq."""
    llm_config = {
        "config_list": get_llm_config(),
        "cache_seed": None,
    }

    agent = autogen.ConversableAgent(
        name=name,
        system_message=system_message,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    if tools:
        for tool in tools:
            agent.register_function(
                function_map={tool.__name__: tool},
            )
            logger.info(f"Registered tool {tool.__name__} for agent {name}")

    return agent