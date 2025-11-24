from openai import OpenAI

class AgentBase:
    def __init__(self, name, system_prompt, model="gpt-4.1"):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.client = OpenAI()

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
