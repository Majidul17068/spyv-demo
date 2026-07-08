from __future__ import annotations

import os
import time

from dotenv import load_dotenv

from spyv import watch

load_dotenv()


@watch(label="router")
def route(query: str) -> str:
    time.sleep(0.15)
    if any(word in query.lower() for word in ("balance", "transfer", "money")):
        return "banking"
    if any(word in query.lower() for word in ("bug", "error", "broken", "refund")):
        return "support"
    return "general"


@watch(label="banking_agent")
def banking_agent(query: str) -> str:
    time.sleep(0.4)
    return "Your balance is $4,210.55."


@watch(label="support_agent")
def support_agent(query: str) -> str:
    time.sleep(0.35)
    return "I've opened ticket #4471 for you."


@watch(label="general_agent")
def general_agent(query: str) -> str:
    time.sleep(0.2)
    return "Happy to help — could you tell me more?"


@watch(label="flaky_agent")
def flaky_agent(query: str) -> str:
    time.sleep(0.1)
    raise TimeoutError("upstream model timed out after 30s")


AGENTS = {
    "banking": banking_agent,
    "support": support_agent,
    "general": general_agent,
}


def handle(query: str) -> str:
    domain = route(query)
    agent = AGENTS.get(domain, general_agent)
    return agent(query)


def main() -> None:
    os.environ.setdefault("SPYV_OUT", "pretty")
    queries = [
        "What's my account balance?",
        "The app is broken and I want a refund",
        "Tell me a fun fact",
    ]
    for q in queries:
        print(f"\nUSER: {q}")
        answer = handle(q)
        print(f"BOT:  {answer}")

    print("\nSimulating an agent failure:")
    try:
        flaky_agent("trigger a timeout")
    except TimeoutError:
        print("BOT:  (agent raised — captured by spyv.watch above)")


if __name__ == "__main__":
    main()
