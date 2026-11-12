"""Standard-library web search helper using Tiger AI Gateway Gemini citations."""
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> None:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("Usage: python scripts/web_search.py '<query>'", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1].strip()
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "").rstrip("/")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    model = os.environ.get("WEB_SEARCH_MODEL", "gemini-3.8-flash")

    if not base_url:
        print("Missing required environment variable: ANTHROPIC_BASE_URL", file=sys.stderr)
        sys.exit(1)
    if not token:
        print("Missing required environment variable: ANTHROPIC_AUTH_TOKEN", file=sys.stderr)
        sys.exit(1)

    url = f"{base_url}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "web_search_options": {},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Search request failed with HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Search request error: {e}", file=sys.stderr)
        sys.exit(1)

    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    print(message.get("content", ""))

    citations = body.get("citations") or message.get("citations") or []
    if citations:
        print("\nCitations:")
        for c in citations:
            print(f"- {c}")


if __name__ == "__main__":
    main()