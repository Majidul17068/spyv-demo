# spyv-demo

Runnable examples for [spyv](https://pypi.org/project/spyv/) — the prompt-security
testing tool for AI engineers.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then paste your OpenAI key into .env
```

Your key lives only in `.env`, which is gitignored — it is never committed.

## ▶ Try your own prompt (start here)

```bash
python demo_try.py
```

`demo_try.py` is a playground. Open it, edit the three sections at the top —
**your** system prompt, your tools, your test queries — then run. Spyv audits
it across the five pillars, probes it with your queries, and shows how to wrap
your own agent with `@guard`. This is the fastest way to point spyv at your
real work.

## Which demos need a key?

Several demos are **fully offline** — they use spyv's deterministic checks and
need no API key at all:

| Demo | Needs a key? | Shows |
|---|---|---|
| `python guard_demo.py` | ❌ no | `@guard` catches secrets/PII leaked in real agent output at runtime |
| `python checkers_demo.py` | ❌ no | the deterministic checker tier + custom rules + allowlist |
| `python example.py` | partial | full API tour (LLM sections skip without a key) |
| `python analyze_prompt.py` | ✅ yes | five-pillar audit of one prompt |
| `python scan_demo.py` | ✅ yes | scan a whole project |
| `python redteam_demo.py` | ✅ yes | fire the OWASP attack corpus |
| `python live_demo.py` | ✅ yes | interactive attack chat |

## ⭐ Live demo

```bash
python live_demo.py
```

An interactive chat against a bank bot, with Spyv judging every message in
real time. The intended flow for a video:

1. It opens with Spyv's five-pillar report of a deliberately **weak** prompt.
2. Type `attacks` to see sample jailbreaks, then send them one by one — watch
   Spyv flag each turn **PROMPT LEAKED / JAILBROKEN** in red.
3. Type `harden` — Spyv swaps in the fixed prompt and shows the report go green.
4. Send the same attacks again — now Spyv shows **SAFE**. That red→green
   contrast is the story.

Commands inside the chat: `attacks`, `harden`, `report`, `quit`.
Set `SPYV_PROVIDER` / `SPYV_MODEL` in `.env` to run it on Anthropic, Gemini,
or a local model instead of OpenAI.

## ⭐ Red-team demo (fire real attacks)

```bash
python redteam_demo.py
```

Fires the 14-attack OWASP corpus at a deliberately weak bank prompt (expect
several breaches), then at a hardened version (expect them held). The
before/after breach table is the strongest security visual. Uses `SPYV_MODEL`
from `.env` — run on `gpt-4o` for the sharpest results.

## ⭐ Scan a whole project

```bash
python scan_demo.py                 # scans the bundled sample_project/
python scan_demo.py ../personakit-demo   # or point it at any real project
```

Spyv discovers every agent prompt in the target — Python variables, OpenAI
`system` messages, constructor `persona=` args, YAML/JSON configs, and prompt
files — audits each one, and prints a ranked table (worst first) plus the single
fix to make first. The bundled `sample_project/` is designed to show a mix of
`unsafe`, `fix_first`, and `ship` verdicts for the demo.

## 1. Analyze a single prompt

Reads a prompt, sends it to your own LLM, and prints the five-pillar report
(quality, optimization, vulnerability, guardrails, fixes).

```bash
python analyze_prompt.py prompts/bank_assistant.yaml
```

## 2. Track agents at runtime

Wraps each agent with `@spyv.watch` and logs every call — name, duration,
ok/error — to the backend log. No API key needed for the tracking itself.

```bash
python track_agent.py
```

## 3. Compare several prompts

Scores every prompt in `prompts/` and prints a leaderboard so you can see
which prompt is strongest before shipping.

```bash
python compare_prompts.py
```

## What each pillar tells you

- **Quality** — is the prompt clear, unambiguous, well-scoped?
- **Optimization** — is it bloated? how many tokens (and dollars) can you save?
- **Vulnerability** — injection, jailbreak, data-leak, tool-misuse exposure (OWASP LLM tags)
- **Guardrails** — which safety rules exist, how strong, how bypassable, what's missing
- **Fixes** — copy-paste-ready edits that close the findings

Bring your own model — spyv reuses your OpenAI client. No extra keys, no extra bills.
