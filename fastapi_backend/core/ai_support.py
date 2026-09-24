"""
core/ai_support.py
-----------------------
Generates a reply for the AI Support Chat widget.

Two modes, chosen automatically:
  - OPENAI_API_KEY set in .env  → calls the OpenAI API for a real reply,
    with the FAQ list as system-prompt context so it stays on-topic for
    this platform specifically.
  - OPENAI_API_KEY blank (default) → keyword-matched canned answers
    covering the 7 topics in the task brief. No external calls, no cost,
    fully deterministic — good for demos and for development without an
    API key.

Same "logs/falls back instead of failing the request" philosophy as
core/email.py: a broken or missing AI integration should degrade to a
still-useful response, not a 500 error for the user asking for help.
"""

import logging

from core.config import settings

logger = logging.getLogger("ai_support")

SYSTEM_PROMPT = (
    "You are a friendly, concise support assistant for a blogging platform "
    "with subscriptions and billing. Answer clearly in 2-4 sentences. "
    "Topics you help with: creating/editing/deleting posts, how subscriptions "
    "and plan limits work, billing and invoices, profile management, "
    "the analytics dashboard, and general platform FAQs."
)

# Ordered (keyword_list, canned_answer) pairs — first match wins. Keep the
# most specific keyword sets earlier so e.g. "delete" doesn't get caught by
# a more generic "post" rule first.
_FAQ_RULES: list[tuple[list[str], str]] = [
    (
        ["delete", "remove post"],
        "To delete a post, open it from your Dashboard or the Posts list and use the delete option — "
        "only the post's original author can delete it. This also removes its comments, likes, and images.",
    ),
    (
        ["edit", "update post"],
        "You can edit a post you created from its detail page — update the title, content, or images, then save. "
        "Only the post's author can edit it.",
    ),
    (
        ["create post", "new post", "write a post", "publish"],
        "To create a post, go to \"New Post\" in the navigation bar, fill in a title and content, "
        "optionally attach image(s), and hit Publish. How many images you can attach depends on your subscription plan.",
    ),
    (
        ["subscription", "plan", "upgrade", "premium", "basic plan", "pro plan"],
        "There are three plans — Basic, Premium, and Pro — each with different limits on posts, images per post, "
        "and daily likes/comments. You can view and change your plan from the Subscriptions page; "
        "upgrading immediately raises your limits.",
    ),
    (
        ["billing", "invoice", "payment", "charge", "price", "receipt"],
        "Every subscription generates an invoice you can view from your billing history, including the plan, "
        "price, and billing period. If something looks wrong with a charge, check your invoice's transaction ID first.",
    ),
    (
        ["profile", "account settings", "change email", "change password", "my account"],
        "You can manage your profile details from your account settings. If you don't see an option you need there, "
        "let us know what you're trying to change and we can point you to the right place.",
    ),
    (
        ["dashboard", "analytics", "stats", "statistics", "views", "chart"],
        "Your Dashboard shows your total posts, comments made, likes received, and post views, plus charts "
        "breaking down likes/comments per post and activity over time — all based on your own account's data.",
    ),
    (
        ["comment"],
        "You can comment on any public post from its detail page. You'll need to be logged in, and your daily "
        "comment limit depends on your subscription plan.",
    ),
    (
        ["like"],
        "You can like any post from its detail page using the heart button. Your daily like limit depends on "
        "your subscription plan, and Pro has no limit.",
    ),
]

_FALLBACK_ANSWER = (
    "I can help with creating/editing/deleting posts, subscriptions and billing, your profile, "
    "and your dashboard analytics. Could you tell me a bit more about what you're trying to do?"
)


def _mocked_reply(message: str) -> str:
    lower = message.lower()
    for keywords, answer in _FAQ_RULES:
        if any(kw in lower for kw in keywords):
            return answer
    return _FALLBACK_ANSWER


def _openai_reply(message: str) -> str:
    from openai import OpenAI  # imported lazily so the package is only required in this mode

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        max_tokens=300,
    )
    return completion.choices[0].message.content.strip()


def get_ai_reply(message: str) -> str:
    """Never raises — falls back to the mocked FAQ answer on any error, including a missing API key."""
    if not settings.OPENAI_API_KEY:
        return _mocked_reply(message)

    try:
        return _openai_reply(message)
    except Exception:
        logger.exception("OpenAI call failed — falling back to mocked FAQ reply")
        return _mocked_reply(message)