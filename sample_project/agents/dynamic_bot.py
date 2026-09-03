"""DEMO FIXTURE -- the spectrum of prompt construction styles.

Real codebases do not write every prompt as a literal. This file contains one
example of each construction style spyv classifies, so the visibility and ladder
demos have something to measure. Nothing here is insecure; it is about whether a
static reader can *see* the prompt at all.

The classifications spyv should produce:

  static   -- the text is in the source, recoverable by reading it
  partial  -- a literal skeleton with runtime holes (an f-string)
  opaque   -- the text is not in the source at this location
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

# --- static: a plain literal ------------------------------------------------
GREETER_PROMPT = "You are a greeter. Welcome the user warmly and briefly."


# --- static via one hop: a name bound to a literal --------------------------
_ROLE = "senior compliance analyst"
ANALYST_PROMPT = _ROLE  # constant propagation reaches this; pure literal extraction does not


def build_persona(domain: str, tone: str) -> str:
    """Assemble a persona at runtime. The result is not in the source."""
    return f"You are an expert in {domain}. Answer in a {tone} register."


def make_agent_prompts(user_tier: str, task: str) -> dict[str, str]:
    """Every style in one place, so a reader can compare them."""

    # partial: literal skeleton, runtime hole. A scanner can read the frame but
    # not what lands in it -- which is exactly where injected text would go.
    tiered_prompt = f"You are a support agent for a {user_tier} customer. Be concise."

    # opaque: the text comes from a callee whose return value depends on inputs.
    persona_prompt = build_persona(os.environ.get("DOMAIN", "tax law"), "formal")

    # opaque: the instruction text arrives as a parameter. This is the
    # agent-to-agent delegation shape -- one component hands another its
    # instructions, and no source-level reader can know what they say.
    delegated_prompt = task

    # opaque: loaded from configuration at runtime. Not in any Python source.
    cfg = Path(__file__).parent.parent / "config" / "triage.yaml"
    config_prompt = yaml.safe_load(cfg.read_text())["system_prompt"] if cfg.exists() else ""

    return {
        "static_literal": GREETER_PROMPT,
        "static_one_hop": ANALYST_PROMPT,
        "partial_fstring": tiered_prompt,
        "opaque_builder": persona_prompt,
        "opaque_parameter": delegated_prompt,
        "opaque_config": config_prompt,
    }
