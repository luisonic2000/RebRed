"""Draft persistence, independent of Tk widgets."""
def draft_key(community, creator):
    return f"{community.casefold()}\u001f{creator.casefold()}"


def store_draft(data, community, creator, title, body, images):
    data.setdefault("drafts", {})[draft_key(community, creator)] = {
        "title": title, "body": body, "images": [str(path) for path in images],
    }


def get_draft(data, community, creator):
    return data.get("drafts", {}).get(draft_key(community, creator), {})
