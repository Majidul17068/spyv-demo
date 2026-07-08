from __future__ import annotations

import os
import sys

import yaml
from dotenv import load_dotenv

from spyv import analyze, terminal

load_dotenv()


class OpenAIClient:
    def __init__(self) -> None:
        import openai

        self._client = openai.OpenAI()

    def chat_completion(self, *, model: str, system: str, user: str, temperature: float = 0.0) -> str:
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY in .env first (copy .env.example).", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1] if len(sys.argv) > 1 else "prompts/bank_assistant.yaml"
    model = os.environ.get("SPYV_MODEL", "gpt-4o")

    with open(path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    print(f"Analyzing {path} with {model} ...\n")
    report = analyze(
        system_prompt=spec["system_prompt"],
        llm=OpenAIClient(),
        model=model,
        tools=spec.get("tools"),
        retrieval_sources=spec.get("retrieval_sources"),
        nshot_examples=spec.get("nshot_examples"),
    )
    terminal.render_report(report)


if __name__ == "__main__":
    main()
