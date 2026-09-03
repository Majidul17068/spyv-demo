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

## ▶ Start here: the whole toolkit against one live agent

```bash
python live_suite.py          # no API key needed
```

`live_agent.py` is a real agent — system prompt, tool registry, dispatch loop,
conversation memory. `live_suite.py` runs it through a real conversation and
then points every spyv capability at that same running subject:

1. **run it** — a genuine conversation, with genuine tool calls
2. **observe it** — which prompts actually reached the model, captured live
3. **check what it said** — deterministic checkers on real output
4. **check what it did** — tool-call policy on the real call trace
5. **check what's readable** — how much prompt surface a scanner can even see
6. **fix and gate** — harden the prompt, watch breaches and violations go to zero

Because every step examines the same agent, the findings connect instead of
sitting in unrelated examples. Set `OPENAI_API_KEY` for real completions; without
one the replies are scripted, but the message objects are still constructed, so
step 2 observes real prompt construction either way.

## ▶ Try your own prompt

```bash
python demo_try.py
```

`demo_try.py` is a playground. Open it, edit the three sections at the top —
**your** system prompt, your tools, your test queries — then run. Spyv audits
it across the five pillars, probes it with your queries, and shows how to wrap
your own agent with `@guard`. This is the fastest way to point spyv at your
real work.

## Which demos need a key?

Most of spyv works with **no key at all** — every deterministic check, every
measurement, and all of the runtime observation.

| Demo | Needs a key? | Shows |
|---|---|---|
| `python live_suite.py` | ❌ no | **everything, against one live agent** |
| `python policy_demo.py` | ❌ no | tool-call policy — all six rule kinds |
| `python visibility_demo.py` | ❌ no | how much prompt surface is readable, and why not |
| `python sarif_demo.py` | ❌ no | SARIF 2.1.0 export + CI gate (exits non-zero) |
| `python guard_demo.py` | ❌ no | `@guard` catches secrets/PII leaked in real agent output at runtime |
| `python checkers_demo.py` | ❌ no | the deterministic checker tier + custom rules + allowlist |
| `python track_agent.py` | ❌ no | `@watch` logs every agent call |
| `python example.py` | partial | full API tour (LLM sections skip without a key) |
| `python analyze_prompt.py` | ✅ yes | five-pillar audit of one prompt |
| `python scan_demo.py` | ✅ yes | scan a whole project |
| `python redteam_demo.py` | ✅ yes | fire the OWASP attack corpus |
| `python live_demo.py` | ✅ yes | interactive attack chat |

### ⭐ Tool-call policy (no key)

```bash
python policy_demo.py
```

A prompt audit tells you what the agent was *told*. A policy tells you what it
*did*. The second is decidable, so it needs no model: `deny`, `arg_limit`,
`require_confirmation`, `require_auth`, `require_precedes` and
`no_secret_in_arguments`, evaluated against a real call trace. Same input, same
verdict, every run — which is the only kind of check that belongs in a merge gate.

### ⭐ What can a scanner even read? (no key)

```bash
python visibility_demo.py                 # bundled sample_project/
python visibility_demo.py ../some-project # or any real codebase
```

Every prompt-security tool starts by extracting prompts from source, and that
first step is usually assumed to work. This measures it: each prompt site is
classified `static`, `partial` or `opaque`, and the opaque ones are broken down
by *why* they resist. It then runs five analysers of increasing strength to show
whether a better parser would help, and splits production code from test and
example code — because scaffolding writes prompts as literals and pooling the
two flatters the number.

### ⭐ SARIF and CI (no key)

```bash
python sarif_demo.py      # exits 1 when an unsafe prompt is found
```

Findings in the format GitHub code scanning already reads, with stable
fingerprints so a scanner can say *new since last run* instead of re-reporting
everything on every commit.

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
