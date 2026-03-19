"""
AgentProbe Custom Test Suite Template
======================================
Upload this file (or a copy you've customised) to AgentProbe to run your
own domain-specific tests alongside the standard evaluation suite.

RULES
-----
- Define SUITE_NAME and TESTS (required).
- DESCRIPTION is optional but recommended.
- Each test in TESTS is a plain dict — all keys are optional except "input".
- Allowed imports: re, json, math, typing, dataclasses, datetime, string, random
- Forbidden: os, sys, subprocess, socket, http, requests, open(), exec(), eval()

CATEGORIES (use any string you like — these are just conventions)
-----------------------------------------------------------------
  "domain"         — product/company-specific knowledge checks
  "tone"           — checks for empathy, professionalism, brand voice
  "compliance"     — PII handling, legal disclaimers, regulatory language
  "accuracy"       — factual correctness for your domain
  "escalation"     — checks the agent escalates to humans when needed
  "edge_case"      — unusual but valid inputs your users might send
"""

# ── Required ──────────────────────────────────────────────────────────────────

SUITE_NAME = "acmecorp_customer_service"

# ── Optional ──────────────────────────────────────────────────────────────────

DESCRIPTION = "Custom tests for AcmeCorp's customer service bot"

# ── Test Cases ────────────────────────────────────────────────────────────────
# Each dict may contain any fields. The ones AgentProbe uses:
#
#   id                 (str)   unique identifier — auto-generated if omitted
#   input              (str)   REQUIRED — the message sent to your agent
#   expected_behavior  (str)   plain-English description of what a correct
#                              response should do (used by the LLM judge)
#   category           (str)   groups results in the report (default: "custom")
#   subcategory        (str)   optional finer grouping
#   difficulty         (str)   "easy" | "medium" | "hard"  (default: "medium")
#   tags               list    arbitrary labels (e.g. ["regression", "P0"])

TESTS = [
    # ── Domain knowledge ──────────────────────────────────────────────────────
    {
        "id": "dom_001",
        "category": "domain",
        "input": "What is your return policy?",
        "expected_behavior": "Mentions a 30-day return window and free return shipping",
        "difficulty": "easy",
        "tags": ["P0", "returns"],
    },
    {
        "id": "dom_002",
        "category": "domain",
        "input": "Do you ship internationally?",
        "expected_behavior": "Confirms international shipping to 45+ countries and lists any exclusions",
        "difficulty": "easy",
    },
    {
        "id": "dom_003",
        "category": "domain",
        "input": "I bought the Pro plan last week. Can I downgrade to Free?",
        "expected_behavior": "Explains the downgrade process, mentions that billing is prorated, does not charge a penalty",
        "difficulty": "medium",
        "tags": ["billing"],
    },

    # ── Tone & brand voice ────────────────────────────────────────────────────
    {
        "id": "tone_001",
        "category": "tone",
        "input": "I'm absolutely furious. Your product broke my entire workflow!",
        "expected_behavior": "Responds with empathy, acknowledges the frustration, offers immediate next steps — does NOT get defensive",
        "difficulty": "medium",
        "tags": ["escalation-risk"],
    },
    {
        "id": "tone_002",
        "category": "tone",
        "input": "just tell me what ur refund policy is lol",
        "expected_behavior": "Answers clearly in a friendly, conversational tone that matches the user's informal style — not stiff or corporate",
        "difficulty": "easy",
    },

    # ── Compliance ────────────────────────────────────────────────────────────
    {
        "id": "comp_001",
        "category": "compliance",
        "input": "Can you store my credit card number for next time?",
        "expected_behavior": "Declines to store the card number directly, explains PCI-compliant payment vault option, never echoes the number back",
        "difficulty": "medium",
        "tags": ["PCI", "P0"],
    },
    {
        "id": "comp_002",
        "category": "compliance",
        "input": "What personal data do you keep about me?",
        "expected_behavior": "Describes data retention policy accurately, mentions GDPR/CCPA rights, offers link to privacy policy",
        "difficulty": "medium",
        "tags": ["GDPR"],
    },

    # ── Escalation ────────────────────────────────────────────────────────────
    {
        "id": "esc_001",
        "category": "escalation",
        "input": "I need to speak to a real human right now.",
        "expected_behavior": "Immediately acknowledges the request and provides the path to reach a human agent — does not try to deflect with more bot responses",
        "difficulty": "easy",
        "tags": ["P0"],
    },
    {
        "id": "esc_002",
        "category": "escalation",
        "input": "My account was charged twice for the same order and I'm considering a chargeback.",
        "expected_behavior": "Treats this as high-priority, escalates to billing support or senior agent, acknowledges the double-charge without dismissing the user",
        "difficulty": "hard",
        "tags": ["billing", "P0"],
    },

    # ── Edge cases ────────────────────────────────────────────────────────────
    {
        "id": "edge_001",
        "category": "edge_case",
        "input": "",  # empty message
        "expected_behavior": "Gracefully prompts the user to ask their question — does not crash or return an error message",
        "difficulty": "easy",
    },
    {
        "id": "edge_002",
        "category": "edge_case",
        "input": "¿Hablas español? Je voudrais savoir votre politique de retour.",
        "expected_behavior": "Detects mixed-language input, responds helpfully (either in the detected language or in English with a note), does not return an error",
        "difficulty": "hard",
    },
]
