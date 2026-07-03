def format_curl(url: str, cookie: str) -> str:
    """生成浏览器风格的 curl 命令，包含完整请求头"""
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
    base = url.split("?")[0]

    lines = [
        f"curl '{url}' \\",
        f"  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \\",
        f"  -H 'accept-language: zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6' \\",
        f"  -H 'cache-control: max-age=0' \\",
        f"  -b '{cookie}' \\",
        f"  -H 'priority: u=0, i' \\",
        f"  -H 'referer: {base}' \\",
        f"  -H 'sec-ch-ua: \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"' \\",
        f"  -H 'sec-ch-ua-mobile: ?0' \\",
        f"  -H 'sec-ch-ua-platform: \"Windows\"' \\",
        f"  -H 'sec-fetch-dest: document' \\",
        f"  -H 'sec-fetch-mode: navigate' \\",
        f"  -H 'sec-fetch-site: same-origin' \\",
        f"  -H 'sec-fetch-user: ?1' \\",
        f"  -H 'upgrade-insecure-requests: 1' \\",
        f"  -H 'user-agent: {ua}'",
    ]
    return "\n".join(lines)
