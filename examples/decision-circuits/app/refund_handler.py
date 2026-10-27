"""A small refund handler that decides with keyword lists and regexes.

This file is a fixture for `tokn circuit detect`. It is never run.
"""
import re

ANGRY_WORDS = ["chargeback", "lawyer", "sue", "scam", "terrible", "never again"]
DAMAGE_PATTERN = re.compile(r"\b(broken|cracked|damaged|faulty)\b", re.IGNORECASE)


def route_refund(message: str, order_total: float, llm) -> str:
    text = message.lower()
    if order_total >= 500:
        return "manager_review"
    if any(word in text for word in ANGRY_WORDS):
        return "human_review"
    if DAMAGE_PATTERN.search(message):
        return "auto_refund"
    reply = llm.complete("Is this customer asking for a refund because they changed their mind? Answer yes or no.\n" + message)
    if "yes" in reply.lower():
        return "store_credit"
    sentiment = llm.sentiment(message)
    if sentiment < 0.35:
        return "human_review"
    return "store_credit"
