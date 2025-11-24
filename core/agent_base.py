import os
from openai import OpenAI

class AgentBase:
    def __init__(self, name, system_prompt, model="gpt-4.1", api_key: str | None = None):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Set it in the environment or pass api_key explicitly."
            )
        self.client = OpenAI(api_key=self.api_key)

    def run(self, user_prompt, context=None):
        """Invoke the LLM with optional conversational context."""
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": user_prompt})


        resp = self.client.responses.create(
            model=self.model,
            input=messages,
        )
        return resp.output_text
