#!/usr/bin/env python3
"""
llm_council_mcp - local MCP (Model Context Protocol) server.

Exposes one tool, `ask_council`, that runs the 3-stage LLM Council
workflow (see council_core.py for the faithful port of the original
llm-council-plus prompts/logic) directly against OpenRouter.

Runs locally via stdio - no Docker, no NAS, no network dependency other
than reaching https://openrouter.ai. Designed to be registered as an MCP
server in Claude Code, Codex CLI, and Google Antigravity (see README.md
for the exact registration steps for each).

Usage (manual smoke test):
    python3 server.py
    (then send MCP stdio messages, or use `npx @modelcontextprotocol/inspector python3 server.py`)
"""

import logging
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, ConfigDict, Field

import council_core
import council_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_council_mcp")

mcp = FastMCP("llm_council_mcp")
mcp._mcp_server.version = "0.1.2"


class AskCouncilInput(BaseModel):
    """Input for ask_council."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str = Field(
        ...,
        description=(
            "The question or decision you want multiple LLMs to weigh in on, "
            "e.g. 'Should we use approach A or B for the caching layer, given "
            "the code below?'. Be specific - the council only sees what's in "
            "this field plus code_context, nothing else about your project."
        ),
        min_length=1,
        max_length=20000,
    )
    code_context: Optional[str] = Field(
        default=None,
        description=(
            "Relevant code, file excerpts, error messages, or other context "
            "the council should consider. Paste actual content here - the "
            "council has no filesystem access of its own; you (the calling "
            "agent) already have the files open, so include what's relevant."
        ),
        max_length=100000,
    )
    models: Optional[List[str]] = Field(
        default=None,
        description=(
            "Optional override list of OpenRouter model IDs to use as council "
            "members, e.g. ['openai/gpt-5.1', 'anthropic/claude-sonnet-4.5', "
            "'x-ai/grok-4']. If omitted, uses the configured default models."
        ),
    )
    chairman: Optional[str] = Field(
        default=None,
        description=(
            "Optional override for the chairman model that synthesizes the "
            "final answer. If omitted, uses the configured default chairman model."
        ),
    )


@mcp.tool(
    name="ask_council",
    annotations={
        "title": "Ask the LLM Council",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ask_council(params: AskCouncilInput, ctx: Context) -> str:
    """Get a multi-model "second opinion" on an important decision.

    Runs the full 3-stage council process locally and synchronously:
      1. Each council model (3 by default) answers the question independently,
         in parallel.
      2. Each model anonymously reviews and ranks the others' answers
         (so a model can't recognize or favor its own response).
      3. A chairman model reads everything from stages 1 and 2 and writes one
         final, synthesized answer. If the chairman call fails, the code
         automatically falls back to trying other council models as chairman
         until one succeeds.


    Returns:
        str: A Markdown report. Starts with the chairman's final synthesized
        answer, followed by each individual council member's Stage-1 response
        for transparency (including which model served as chairman, and
        whether a fallback chairman had to be used).

    Error Handling:
        - Returns "Error: ..." if the API key is missing or invalid.
        - Returns "Error: ..." if every council model failed in Stage 1, or if
          the chairman and all fallback chairmen failed in Stage 3.
        - Individual model failures in Stage 1/2 are reported inline but do
          not block the overall result as long as at least one model succeeds.

    Based on Andrej Karpathy's "LLM Council" idea (github.com/karpathy/llm-council).
    MCP server by Alexander Deja (anderzlabs.de).
    """
    logger.info("Starting council query. Models override: %s", params.models)

    async def _progress(progress: float, total: float, msg: str):
        await ctx.info(msg)
        if hasattr(ctx, "report_progress"):
            try:
                await ctx.report_progress(progress, total)
            except Exception:
                pass

    try:
        result = await council_core.run_full_council(
            user_query=params.question,
            code_context=params.code_context,
            models=params.models,
            chairman=params.chairman,
            progress_callback=_progress,
        )
    except council_core.CouncilError as e:
        return f"Error: {e}"
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error running the council")
        return f"Error: unexpected failure running the council: {e}"

    stage3 = result["stage3"]
    if stage3.get("error"):
        return stage3.get("response")

    lines: List[str] = ["# Council Verdict", ""]

    chairman_label = stage3["model"]
    if stage3.get("fallback_used"):
        lines.append(
            f"**Chairman:** {chairman_label} "
            f"_(fallback - original chairman {stage3.get('original_chairman')} failed)_"
        )
    else:
        lines.append(f"**Chairman:** {chairman_label}")
    lines += ["", stage3["response"], "", "---", "", "## Individual council responses (Stage 1)", ""]

    for r in result["stage1"]:
        if r.get("error"):
            lines.append(f"### {r['model']} — failed")
            lines.append(f"_{r.get('error_message', 'unknown error')}_")
        else:
            lines.append(f"### {r['model']}")
            lines.append(r["response"])
        lines.append("")

    if result["stage2"]:
        lines += ["---", "", "## Peer rankings (Stage 2)", ""]
        for r in result["stage2"]:
            if r.get("error"):
                lines.append(f"### {r['model']} — failed to rank")
                lines.append(f"_{r.get('error_message', 'unknown error')}_")
            else:
                parsed = r.get("parsed_ranking") or []
                if parsed:
                    lines.append(f"### {r['model']} ranked: {' > '.join(parsed)}")
                else:
                    lines.append(f"### {r['model']}")
            lines.append("")

    return "\n".join(lines)


def _maybe_start_setup_ui() -> None:
    try:
        # Load settings
        settings = council_settings.load_settings()
        # Default is True if not present
        if not settings.get("open_ui_on_start", True):
            return

        host = "127.0.0.1"
        port = 5151
        target_port = None
        should_start_ui = False
        should_open_browser = True

        import socket
        def is_port_in_use(p: int) -> bool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                return s.connect_ex((host, p)) == 0

        def is_our_ui(p: int) -> bool:
            import urllib.request
            try:
                url = f"http://{host}:{p}/__ping__"
                with urllib.request.urlopen(url, timeout=0.5) as response:
                    if response.status == 200:
                        return response.read().decode('utf-8').strip() == "llm-council"
            except Exception:
                pass
            return False

        if is_port_in_use(port):
            if is_our_ui(port):
                target_port = port
                should_start_ui = False
            else:
                for fallback_port in range(5152, 5161):
                    if not is_port_in_use(fallback_port):
                        target_port = fallback_port
                        should_start_ui = True
                        break
                else:
                    should_open_browser = False
        else:
            target_port = port
            should_start_ui = True

        if should_start_ui and target_port:
            import threading
            def run_flask():
                try:
                    import logging
                    logging.getLogger("werkzeug").setLevel(logging.ERROR)
                    try:
                        import flask.cli
                        flask.cli.show_server_banner = lambda *x: None
                    except Exception:
                        pass

                    from setup_ui import app
                    app.run(host=host, port=target_port, debug=False, use_reloader=False)
                except Exception:
                    pass

            t = threading.Thread(target=run_flask, daemon=True)
            t.start()

        if should_open_browser and target_port:
            import threading
            def open_browser():
                try:
                    import webbrowser
                    webbrowser.open(f"http://{host}:{target_port}")
                except Exception:
                    pass

            threading.Timer(1.0, open_browser).start()
    except Exception:
        pass


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config-dir", type=str)
    
    args, remaining = parser.parse_known_args()
    
    if args.config_dir:
        council_settings.set_config_dir_override(args.config_dir)
        
    sys.argv = [sys.argv[0]] + remaining
    _maybe_start_setup_ui()
    mcp.run()

if __name__ == "__main__":
    main()
