import os
import sys

from dotenv import load_dotenv

from server.src.search.mcp_search import create_mcp_server, _init_gemini


def main() -> int:
    load_dotenv()
    try:
        _init_gemini()
    except Exception as e:
        print("Failed to init Gemini:", e)
        return 1

    mcp = create_mcp_server()
    prompt = os.environ.get("GEMINI_PROMPT", "Say hello from Gemini.")
    text = mcp.gemini_generate(prompt)  # type: ignore[attr-defined]
    print("Gemini:", text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


