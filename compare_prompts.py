from __future__ import annotations

import glob
import os
import sys

import yaml
from dotenv import load_dotenv

from spyv import analyze

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
        print("Set OPENAI_API_KEY in .env first.", file=sys.stderr)
        sys.exit(1)

    model = os.environ.get("SPYV_MODEL", "gpt-4o")
    client = OpenAIClient()
    rows = []

    for path in sorted(glob.glob("prompts/*.yaml")):
        with open(path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        report = analyze(
            system_prompt=spec["system_prompt"],
            llm=client,
            model=model,
            tools=spec.get("tools"),
            retrieval_sources=spec.get("retrieval_sources"),
        )
        rows.append((
            os.path.basename(path),
            report.overall_score,
            report.overall_verdict,
            report.quality.score,
            report.guardrails.score,
            len(report.vulnerabilities),
            len(report.fixes),
        ))

    print(f"\n{'prompt':<28}{'overall':>8}{'verdict':>12}{'quality':>9}{'guard':>7}{'vulns':>7}{'fixes':>7}")
    print("-" * 78)
    for name, overall, verdict, quality, guard, vulns, fixes in rows:
        print(f"{name:<28}{overall:>8.1f}{verdict:>12}{quality:>9.1f}{guard:>7.1f}{vulns:>7}{fixes:>7}")


if __name__ == "__main__":
    main()
