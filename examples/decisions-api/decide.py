"""Ask typed questions with the Decisions API (POST /v1/decisions).

Usage:
  python decide.py "I was charged twice for my order. Please return the extra charge."

Backend selection (environment only, never hard-coded):
  OpenAI:        OPENAI_API_KEY
  Azure OpenAI:  AZURE_OPENAI_ENDPOINT = https://<resource>.openai.azure.com/openai/v1/
                 AZURE_OPENAI_API_KEY  (or AZURE_OPENAI_USE_ENTRA=1 after `az login`)
                 DECISIONS_MODEL       = your gpt-6-luna deployment name
Needs: pip install "openai>=2.0" (and azure-identity for Entra ID).
"""

import os
import sys

try:
    from openai import OpenAI
except ImportError:
    sys.exit('missing dependency: pip install "openai>=2.0" (azure-identity too for Entra ID)')

QUESTIONS = [
    {
        "type": "predicate",
        "name": "refund_requested",
        "instructions": "Does the customer ask for a refund?",
    },
    {
        "type": "predicate",
        "name": "duplicate_charge",
        "instructions": "Does the customer report being charged more than once for the same order?",
    },
    {
        "type": "predicate",
        "name": "threatens_chargeback",
        "instructions": "Does the customer say they will dispute the charge with their bank?",
    },
]


def make_client():
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        if not os.environ.get("OPENAI_API_KEY"):
            sys.exit("set OPENAI_API_KEY, or AZURE_OPENAI_ENDPOINT for Azure OpenAI")
        return OpenAI()
    if not endpoint.rstrip("/").endswith("/openai/v1"):
        sys.exit("AZURE_OPENAI_ENDPOINT must end in /openai/v1/, e.g. https://<resource>.openai.azure.com/openai/v1/")
    key = os.environ.get("AZURE_OPENAI_API_KEY")
    if key:
        return OpenAI(base_url=endpoint, api_key=key)
    if os.environ.get("AZURE_OPENAI_USE_ENTRA") != "1":
        sys.exit("set AZURE_OPENAI_API_KEY, or AZURE_OPENAI_USE_ENTRA=1 to use Microsoft Entra ID")
    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    except ImportError:
        sys.exit("missing dependency for Entra ID: pip install azure-identity")
    token = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    return OpenAI(base_url=endpoint, api_key=token)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    client = make_client()
    decision = client.decisions.create(
        model=os.environ.get("DECISIONS_MODEL", "gpt-6-luna"),
        input=sys.argv[1],
        questions=QUESTIONS,
    )
    for question, answer in zip(QUESTIONS, decision.answers):
        name = question["name"]
        if answer.type == "predicate":
            print(f"{name:22} probability={answer.probability:.2f}")
        elif answer.type == "refusal":
            # A refusal is an answer, not a failure: report it, never guess.
            print(f"{name:22} REFUSED")
        else:
            print(f"{name:22} unexpected answer type {answer.type!r}")


if __name__ == "__main__":
    main()
