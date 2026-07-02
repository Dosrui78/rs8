from urllib.parse import urlparse


def build_environment(profile: dict, url: str) -> dict:
    parsed = urlparse(url)
    env = __deep_copy(profile)

    nav = env.setdefault("navigator", {})
    scr = env.setdefault("screen", {})
    loc = env.setdefault("location", {})

    loc.update({
        "href": url,
        "origin": f"{parsed.scheme}://{parsed.netloc}",
        "protocol": f"{parsed.scheme}:",
        "host": parsed.netloc,
        "hostname": parsed.hostname or "",
        "port": str(parsed.port or ""),
        "pathname": parsed.path or "/",
        "search": f"?{parsed.query}" if parsed.query else "",
        "hash": f"#{parsed.fragment}" if parsed.fragment else "",
    })

    return env


def __deep_copy(d):
    import copy
    return copy.deepcopy(d)
