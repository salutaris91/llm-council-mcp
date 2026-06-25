"""
council_core.py

Standalone, local reimplementation of the 3-stage workflow used by
llm-council-plus (https://github.com/DmitryBMsk/llm-council-plus).

This module talks directly to OpenRouter and has no dependency on Docker,
a NAS, or the original FastAPI backend. It exists so the exact same
prompts and stage order can run locally on a MacBook, called from any
MCP-capable coding agent (Claude Code, Codex CLI, Antigravity, ...).

The 3 stages, faithfully ported from backend/council.py and
backend/runtime_settings.py in the original repo:

  Stage 1 - Each council model answers the question independently.
  Stage 2 - Each model anonymously reviews and ranks the others' answers
            (labelled "Response A", "Response B", ... so models can't
            recognize/favor themselves).
  Stage 3 - A chairman model reads stage 1 + stage 2 and synthesizes one
            final answer. If the chairman call fails, the code falls back
            to trying every model that succeeded in stage 1, in order,
            until one of them produces a synthesis.

What was intentionally left out of this port (judged non-essential for a
personal, local tool; see README for details):
  - TOON encoding of stage1/stage2 data (a token-efficiency optimization
    in the original; plain text is used here instead)
  - Web search / tool-result injection into stage 1
  - Persisted runtime settings file / settings UI (prompts are constants
    here; edit this file directly if you want to change them)
  - Conversation history / multi-turn memory
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Callable, Awaitable

import httpx
import council_settings

logger = logging.getLogger("llm_council_core")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Retry/backoff constants, ported from backend/openrouter.py.
MAX_RETRIES = 2
INITIAL_BACKOFF_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 30.0

DEFAULT_TIMEOUT_SECONDS = 120.0

# ---------------------------------------------------------------------------
# Prompt templates - copied verbatim from backend/runtime_settings.py
# (DEFAULT_STAGE1_PROMPT_TEMPLATE / DEFAULT_STAGE2_PROMPT_TEMPLATE /
# DEFAULT_STAGE3_PROMPT_TEMPLATE). Do not reword these without checking
# against the upstream repo - the stage2 ranking parser below depends on
# the exact "FINAL RANKING:" / "Response X" format the stage2 prompt asks
# for.
# ---------------------------------------------------------------------------

STAGE1_PROMPT_TEMPLATE = "{full_query}"

STAGE2_PROMPT_TEMPLATE = """You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example of the correct format for your ENTIRE response:

Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""

STAGE3_PROMPT_TEMPLATE = """You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

{rankings_block}{tools_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality (if available)
- Any patterns of agreement or disagreement

Provide a clear, well-reasoned final answer that represents the council's collective wisdom:"""


class CouncilError(Exception):
    """Raised for configuration problems (e.g. missing API key)."""





# ---------------------------------------------------------------------------
# Low-level OpenRouter call, with retry/backoff on 429, matching
# backend/openrouter.py's query_model().
# ---------------------------------------------------------------------------

async def _query_model(
    client: httpx.AsyncClient,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float,
    api_key: str,
    max_tokens: int,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """Call a single model via OpenRouter. Returns {'content': str} or
    {'error': True, 'error_message': str}. Never raises for HTTP/network
    errors - callers treat a failed model as "skip it, keep going",
    matching the original's resilience to partial failures.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        payload["temperature"] = temperature

    backoff = INITIAL_BACKOFF_SECONDS
    last_error: Optional[str] = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await client.post(
                OPENROUTER_API_URL, headers=headers, json=payload, timeout=timeout
            )
            if resp.status_code == 429 and attempt < MAX_RETRIES:
                last_error = "rate limited (429)"
                logger.warning(
                    "Model %s rate-limited, retrying in %.1fs (attempt %d/%d)",
                    model, backoff, attempt + 1, MAX_RETRIES,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                continue

            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return {"content": content}

        except httpx.HTTPStatusError as e:
            last_error = f"HTTP {e.response.status_code}: {e.response.text[:300]}"
            logger.warning("Model %s failed: %s", model, last_error)
            break
        except httpx.TimeoutException:
            last_error = f"timed out after {timeout}s"
            logger.warning("Model %s: %s", model, last_error)
            break
        except Exception as e:  # noqa: BLE001 - we want to swallow & report
            last_error = str(e)
            logger.warning("Model %s failed: %s", model, last_error)
            break

    return {"error": True, "error_message": last_error or "unknown error"}


async def _query_models_parallel(
    models: List[str],
    messages: List[Dict[str, Any]],
    temperature: float,
    api_key: str,
    max_tokens: int,
) -> Dict[str, Dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        coros = [_query_model(client, model, messages, temperature, api_key, max_tokens) for model in models]
        results = await asyncio.gather(*coros)
        return dict(zip(models, results))


def _parse_ranking_from_text(ranking_text: str) -> List[str]:
    """Extract the ordered list of response labels (e.g. ['Response C',
    'Response A', 'Response B']) from a stage-2 model's ranking text, per
    the "FINAL RANKING:" format requested in STAGE2_PROMPT_TEMPLATE.
    """
    match = re.search(r"FINAL RANKING:\s*\n?(.+)", ranking_text, re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    block = match.group(1)
    return re.findall(r"\d+\.\s*(Response\s+[A-Z])", block)


# ---------------------------------------------------------------------------
# Stage 1 - collect independent responses
# ---------------------------------------------------------------------------

async def stage1_collect_responses(
    user_query: str,
    code_context: Optional[str],
    models: List[str],
    api_key: str,
    max_tokens: int,
    t1: float,
) -> List[Dict[str, Any]]:
    full_query = user_query
    if code_context and code_context.strip():
        full_query = (
            f"{user_query}\n\n"
            f"--- Relevant code / file context provided by the caller ---\n"
            f"{code_context.strip()}\n"
            f"--- end context ---"
        )

    prompt = STAGE1_PROMPT_TEMPLATE.format(full_query=full_query)
    messages = [{"role": "user", "content": prompt}]

    responses = await _query_models_parallel(models, messages, t1, api_key, max_tokens)

    results: List[Dict[str, Any]] = []
    for model in models:
        response = responses[model]
        if response.get("error"):
            results.append({
                "model": model,
                "error": True,
                "error_message": response.get("error_message"),
            })
        else:
            results.append({"model": model, "response": response.get("content", "")})
    return results


# ---------------------------------------------------------------------------
# Stage 2 - anonymized peer ranking
# ---------------------------------------------------------------------------

async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    api_key: str,
    max_tokens: int,
    t2: float,
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    valid = [r for r in stage1_results if r.get("response") and r["response"].strip()]
    if not valid:
        return [], {}

    labels = [chr(65 + i) for i in range(len(valid))]  # A, B, C, ...
    label_to_model = {f"Response {label}": r["model"] for label, r in zip(labels, valid)}

    responses_text = "\n\n".join(
        f"Response {label}:\n{r['response']}" for label, r in zip(labels, valid)
    )

    ranking_prompt = STAGE2_PROMPT_TEMPLATE.format(
        user_query=user_query, responses_text=responses_text
    )
    messages = [{"role": "user", "content": ranking_prompt}]

    # Only ask models that actually succeeded in stage 1 to rank (mirrors
    # the rate-limit optimization in the original: no point asking a
    # model that just failed to also do the ranking work).
    models_to_ask = [r["model"] for r in valid]
    responses = await _query_models_parallel(models_to_ask, messages, t2, api_key, max_tokens)

    results: List[Dict[str, Any]] = []
    for model in models_to_ask:
        response = responses[model]
        if response.get("error"):
            results.append({
                "model": model,
                "error": True,
                "error_message": response.get("error_message"),
            })
        else:
            text = response.get("content", "")
            results.append({
                "model": model,
                "ranking": text,
                "parsed_ranking": _parse_ranking_from_text(text),
            })
    return results, label_to_model


# ---------------------------------------------------------------------------
# Stage 3 - chairman synthesis, with fallback-chairman logic
# ---------------------------------------------------------------------------

def _build_stage3_prompt(
    user_query: str,
    stage1_valid: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
) -> str:
    stage1_text = "\n\n".join(f"[{r['model']}]\n{r['response']}" for r in stage1_valid)

    rankings_with_text = [r for r in stage2_results if r.get("ranking")]
    if rankings_with_text:
        stage2_text = "\n\n".join(f"[{r['model']}]\n{r['ranking']}" for r in rankings_with_text)
        rankings_block = f"STAGE 2 - Peer Rankings:\n{stage2_text}"
    else:
        rankings_block = (
            "Note: Peer rankings were not available for this query.\n\n"
            "STAGE 2 - Peer Rankings:\n(none)"
        )

    return STAGE3_PROMPT_TEMPLATE.format(
        user_query=user_query,
        stage1_text=stage1_text,
        rankings_block=rankings_block,
        tools_text="",
    )


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    chairman_model: str,
    api_key: str,
    max_tokens: int,
    t3: float,
) -> Dict[str, Any]:
    stage1_valid = [r for r in stage1_results if r.get("response") and r["response"].strip()]
    if not stage1_valid:
        return {
            "model": chairman_model,
            "error": True,
            "response": "Error: no usable Stage 1 responses to synthesize from "
                        "(every council model failed).",
        }

    prompt = _build_stage3_prompt(user_query, stage1_valid, stage2_results)
    messages = [{"role": "user", "content": prompt}]

    async with httpx.AsyncClient() as client:
        primary = await _query_model(client, chairman_model, messages, t3, api_key, max_tokens)
        if not primary.get("error"):
            return {"model": chairman_model, "response": primary["content"]}

        logger.warning(
            "Chairman model %s failed (%s); trying fallback chairmen from stage 1 survivors",
            chairman_model, primary.get("error_message"),
        )

        tried_fallbacks: List[str] = []
        for candidate in stage1_valid:
            fallback_model = candidate["model"]
            if fallback_model == chairman_model:
                continue
            tried_fallbacks.append(fallback_model)
            result = await _query_model(client, fallback_model, messages, t3, api_key, max_tokens)
            if not result.get("error"):
                return {
                    "model": fallback_model,
                    "response": result["content"],
                    "fallback_used": True,
                    "original_chairman": chairman_model,
                }

    return {
        "model": chairman_model,
        "error": True,
        "response": (
            f"Error: chairman model '{chairman_model}' failed and all fallback "
            f"chairmen also failed (tried: {tried_fallbacks})."
        ),
        "tried_fallbacks": tried_fallbacks,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def run_full_council(
    user_query: str,
    code_context: Optional[str] = None,
    models: Optional[List[str]] = None,
    chairman: Optional[str] = None,
    progress_callback: Optional[Callable[[float, float, str], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    """Run all 3 stages in order and return every stage's raw results."""
    
    settings = council_settings.load_settings()
    api_key = settings.get("openrouter_api_key")
    if not api_key:
        raise CouncilError(
            "OPENROUTER_API_KEY is not set. Please set it using the llm-council-setup UI."
        )
        
    try:
        max_tokens = int(settings.get("max_tokens", council_settings.DEFAULT_MAX_TOKENS))
        t1 = float(settings.get("stage1_temperature", council_settings.DEFAULT_STAGE1_TEMPERATURE))
        t2 = float(settings.get("stage2_temperature", council_settings.DEFAULT_STAGE2_TEMPERATURE))
        t3 = float(settings.get("stage3_temperature", council_settings.DEFAULT_STAGE3_TEMPERATURE))
    except ValueError as e:
        raise CouncilError(f"Ungültiger numerischer Wert in den Profi-Einstellungen (bitte korrigieren im UI): {e}")

    async def _report(progress: float, total: float, msg: str):
        if progress_callback:
            await progress_callback(progress, total, msg)

    raw_council_models = models or settings.get("council_models")
    council_models = [m.strip() for m in raw_council_models if m and m.strip()] if raw_council_models else []
    if not council_models:
        council_models = council_settings.DEFAULT_COUNCIL_MODELS
        
    raw_chairman = chairman or settings.get("chairman_model")
    chairman_model = raw_chairman.strip() if raw_chairman and raw_chairman.strip() else council_settings.DEFAULT_CHAIRMAN_MODEL

    await _report(10, 100, f"Stage 1: Collecting responses from {len(council_models)} models...")
    stage1 = await stage1_collect_responses(user_query, code_context, council_models, api_key, max_tokens, t1)
    
    await _report(50, 100, "Stage 2: Peer ranking of responses...")
    stage2, label_to_model = await stage2_collect_rankings(user_query, stage1, api_key, max_tokens, t2)
    
    await _report(80, 100, f"Stage 3: Synthesis by chairman {chairman_model}...")
    stage3 = await stage3_synthesize_final(user_query, stage1, stage2, chairman_model, api_key, max_tokens, t3)
    
    await _report(100, 100, "Council process complete.")

    return {
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "label_to_model": label_to_model,
        "council_models": council_models,
        "chairman_model": chairman_model,
    }
