"""Source-backed constraints. Unlisted packs remain explicitly unverified."""
REVIEW_DATE = "2026-11-03"
PACKS = {
    "drawforme": {"title_prefix": "[Paid Offer] ", "required_title_terms": ["[paid offer]"], "require_handle": False, "no_title_contact": True, "offer_days": ["Sat", "Sun"], "notes": "Paid Offers are limited to one per week and weekends only. Titles must be descriptive and English, without URLs, email, Discord handles or usernames. Review the full paid-offer requirements before posting."},
    "hireanartist": {"require_price": True, "require_portfolio": True, "banned_domains": ["patreon.com", "etsy.com", "redbubble.com"], "notes": "Include a portfolio link and prices. The title must describe what you sell, beyond only a style or commissions open. Use the correct Artist for Hire flair. Showcases and requests for followers are not allowed."},
    "animecommission": {"minimum_personal": 35, "minimum_commercial": 100, "require_price": True, "require_portfolio": True, "require_social": True, "require_handle": True, "title_prefix": "", "banned_title_terms": ["[for hire]", "[commission]"], "banned_domains": ["fiverr.com", "deviantart.com"], "notes": "Include service, price, direct portfolio and secondary social link in the body. Use the correct flair. Discord handles are allowed; continue there after choosing an artist. Image and NSFW rules require manual checking."},
    "starvingartists": {"minimum_personal": 30, "minimum_commercial": 100, "required_title_terms": ["[for hire]"], "title_prefix": "[For Hire] ", "banned_domains": ["instagram.com", "x.com", "twitter.com", "drive.google.com", "fiverr.com"], "notes": "One For Hire post per week. Show a gallery or public portfolio. No external network advertising or posting for someone else. Hiring posts require a budget. Minimums apply per piece."},
    "artcommissions": {"minimum_personal": 20, "minimum_commercial": 100, "require_price": True, "required_title_terms": ["[for hire]"], "title_prefix": "[For Hire] ", "notes": "One ad per 3 days. Include prices and multiple previous works. At least 10 karma is required. Do not disguise ads as discussion or work in progress."},
    "hungryartists": {"minimum_personal": 30, "minimum_commercial": 100, "require_price": True, "required_title_terms": ["[for hire]"], "title_prefix": "[For Hire] ", "notes": "One ad per 7 days. Include prices and previous works. At least 25 post and comment karma required. Full rights transfer has a $500 minimum. Minimums apply per piece."},
    "dnd": {"promotion_allowed": False, "require_price": False, "min_body_chars": 400, "required_title_any_terms": ["[art]", "[oc]"], "banned_domains": ["x.com", "twitter.com"], "manual_description": True, "notes": "Artwork requires a genuine 400+ character description in the body, an Art or OC title tag, and original content not previously posted here. Thursdays are text-only (Eastern US timing). Promotion requires prior mod approval per item and a Comm tag; no price charts. Do not use generated prose as a substitute for your own description."},
}
INTERVALS = {"starvingartists": 168, "artcommissions": 72, "hungryartists": 168, "drawforme": 168}

for name in ("artcommissions", "hungryartists"):
    PACKS[name]["banned_domains"] = ["fiverr.com", "upwork.com", "drive.google.com", "photos.google.com", "dropbox.com", "etsy.com", "redbubble.com", "sites.google.com"]


def apply_evidence(profile):
    name = profile.get("name", "").lower()
    rules = profile.setdefault("rules", {})
    rules.setdefault("source_url", f"https://www.reddit.com/r/{profile.get('name', '')}/about/rules/")
    rules.setdefault("verification_status", "unverified")
    if name not in PACKS or rules.get("evidence_version") == 1:
        return
    # Retain an inspectable copy of the previous constraints and notes.
    profile.setdefault("previous_rule_packs", []).append(dict(rules))
    rules.update(PACKS[name])
    rules.update(last_reviewed=REVIEW_DATE, verification_status="partial", evidence_version=1)
    if name == "dnd":
        rules["source_url"] = "https://www.reddit.com/r/DnD/wiki/rules/"
    rules["evidence"] = {key: {"url": rules["source_url"], "reviewed": REVIEW_DATE, "kind": "requirement"} for key in PACKS[name] if key != "notes"}
    if name in INTERVALS:
        profile["min_interval_hours"] = INTERVALS[name]
