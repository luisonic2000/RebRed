"""Pure helpers shared by draft generation and final checks."""
import re
from datetime import date
from urllib.parse import urlsplit


def unresolved_tokens(text):
    return sorted(set(re.findall(r"\{\{?([a-zA-Z_]\w*)\}?\}", text)))


def blocked_urls(text, domains):
    blocked = set()
    for url in re.findall(r"https?://[^\s<>\)]+", text):
        host = (urlsplit(url).hostname or "").lower()
        if any(host == domain.lower() or host.endswith("." + domain.lower()) for domain in domains):
            blocked.add(url)
    return blocked


def rule_review_due(rules, today=None):
    try:
        reviewed = date.fromisoformat(rules.get("last_reviewed", ""))
    except (TypeError, ValueError):
        return True
    return rules.get("verification_status") != "verified" or ((today or date.today()) - reviewed).days > 90
