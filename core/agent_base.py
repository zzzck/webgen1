import os
from openai import OpenAI

# 设置http和https的代理
os.environ["HTTP_PROXY"] = "http://211.81.248.212:3128"
os.environ["HTTPS_PROXY"] = "http://211.81.248.212:3128"


class AgentBase:
    def __init__(self, name, system_prompt, model="gpt-5-chat-latest", api_key: str | None = None):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Set it in the environment or pass api_key explicitly."
            )
        self.client = OpenAI(api_key=self.api_key, base_url="http://98.81.169.220:3000")

    def run(self, user_prompt, context=None, json_mode: bool = False):
        """Invoke the LLM with optional conversational context.

        The agent's system prompt is always injected as the first message so
        every call uses the agent-specific instructions.
        """
        messages = [
            {"role": "system", "content": [{"type": "text", "text": self.system_prompt}]}
        ]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": [{"type": "text", "text": user_prompt}]})

        resp = self.client.responses.create(
            model=self.model,
            input=messages,
            response_format={"type": "json_object"} if json_mode else None,
        )

        return self._extract_text(resp)

    def _extract_text(self, resp):
        """Normalize different SDK response shapes to a plain string."""
        if resp is None:
            return ""

        # Preferred helper provided by the Responses API.
        output_text = getattr(resp, "output_text", None)
        if output_text:
            return output_text

        # Fallback to concatenating text blocks from the structured output.
        output = getattr(resp, "output", None)
        if output:
            text_chunks = []
            for block in output:
                content = getattr(block, "content", None)
                if not content:
                    continue
                for part in content:
                    text_part = getattr(part, "text", None)
                    if isinstance(text_part, str):
                        text_chunks.append(text_part)
                    else:
                        value = getattr(text_part, "value", None)
                        if value:
                            text_chunks.append(str(value))
            if text_chunks:
                return "\n".join(text_chunks)

        # ChatCompletion-style compatibility.
        choices = getattr(resp, "choices", None)
        if choices:
            for choice in choices:
                message = getattr(choice, "message", None)
                if message:
                    content = getattr(message, "content", None)
                    if content:
                        return content

        # Fall back to the raw string representation so the caller gets something usable
        # even if the SDK response shape changes.
        return str(resp)
