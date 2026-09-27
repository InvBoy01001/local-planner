"""Normalize inbound user text before prompts and model calls."""


def normalize_user_query(query: str) -> str:
    """
    Fix common copy/paste issues (e.g. literal backslash-n instead of newlines)
    and trim trailing whitespace per line.
    """
    if not query:
        return query
    q = query.replace("\\r\\n", "\n").replace("\\r", "\n").replace("\\n", "\n")
    q = "\n".join(line.rstrip() for line in q.splitlines())
    return q.strip()
