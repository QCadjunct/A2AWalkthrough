"""Model registry, derived from ``fabric -L`` output.

Shape mirrors fabric exactly: ``Vendor -> [models]``. Regenerate by pasting a
fresh ``fabric -L`` dump into ``_FABRIC_DUMP`` below and re-importing — no schema
change, no per-model metadata, no scope creep. Adding a model is adding a line.

The registry is the single source of truth for which models each vendor serves.
The cascade decorator (decorators.cascade) validates (vendor, model) pairs
against it; the ModelMessage (messages.py) is the wire form.
"""

from __future__ import annotations

from collections import defaultdict
from types import MappingProxyType

# Paste the raw ``fabric -L`` block here (the "Vendor|model" column). The index
# markers and asterisks fabric prints are tolerated by the parser.
_FABRIC_DUMP = """
Anthropic|claude-haiku-4-5
Anthropic|claude-haiku-4-5-20251001
Anthropic|claude-opus-4-0
Anthropic|claude-opus-4-1-20250805
Anthropic|claude-opus-4-20250514
Anthropic|claude-opus-4-5
Anthropic|claude-opus-4-5-20251101
Anthropic|claude-opus-4-6
Anthropic|claude-opus-4-7
Anthropic|claude-sonnet-4-0
Anthropic|claude-sonnet-4-20250514
Anthropic|claude-sonnet-4-5
Anthropic|claude-sonnet-4-5-20250929
Anthropic|claude-sonnet-4-6
GitHub|ai21-labs/ai21-jamba-1.5-large
GitHub|cohere/cohere-command-a
GitHub|cohere/cohere-command-r-08-2024
GitHub|cohere/cohere-command-r-plus-08-2024
GitHub|deepseek/deepseek-r1
GitHub|deepseek/deepseek-r1-0528
GitHub|deepseek/deepseek-v3-0324
GitHub|meta/llama-3.2-11b-vision-instruct
GitHub|meta/llama-3.2-90b-vision-instruct
GitHub|meta/llama-3.3-70b-instruct
GitHub|meta/llama-4-maverick-17b-128e-instruct-fp8
GitHub|meta/llama-4-scout-17b-16e-instruct
GitHub|meta/meta-llama-3.1-405b-instruct
GitHub|meta/meta-llama-3.1-8b-instruct
GitHub|microsoft/mai-ds-r1
GitHub|microsoft/phi-4
GitHub|microsoft/phi-4-mini-instruct
GitHub|microsoft/phi-4-mini-reasoning
GitHub|microsoft/phi-4-multimodal-instruct
GitHub|microsoft/phi-4-reasoning
GitHub|mistral-ai/codestral-2501
GitHub|mistral-ai/ministral-3b
GitHub|mistral-ai/mistral-medium-2505
GitHub|mistral-ai/mistral-small-2503
GitHub|openai/gpt-4.1
GitHub|openai/gpt-4.1-mini
GitHub|openai/gpt-4.1-nano
GitHub|openai/gpt-4o
GitHub|openai/gpt-4o-mini
GitHub|openai/gpt-5
GitHub|openai/gpt-5-chat
GitHub|openai/gpt-5-mini
GitHub|openai/gpt-5-nano
GitHub|openai/o1
GitHub|openai/o1-mini
GitHub|openai/o1-preview
GitHub|openai/o3
GitHub|openai/o3-mini
GitHub|openai/o4-mini
GitHub|openai/text-embedding-3-large
GitHub|openai/text-embedding-3-small
GitHub|xai/grok-3
GitHub|xai/grok-3-mini
Ollama|deepseek-v3.2:cloud
Ollama|deepseek-v4-flash:cloud
Ollama|deepseek-v4-pro:cloud
Ollama|devstral-small-2:24b-cloud
Ollama|fhagenciadigital/ds-go-pro:latest
Ollama|gemma3:12b
Ollama|gemma4:31b-cloud
Ollama|glm-5.1:cloud
Ollama|kimi-k2.6:cloud
Ollama|minimax-m3:cloud
Ollama|ministral-3:14b-cloud
Ollama|nemotron-3-nano:30b-cloud
Ollama|nemotron-3-super:cloud
Ollama|qwen3-coder-next:cloud
Ollama|qwen3.5:397b-cloud
Ollama|qwen3:8b
Perplexity|r1-1776
Perplexity|sonar
Perplexity|sonar-pro
Perplexity|sonar-reasoning
Perplexity|sonar-reasoning-pro
"""


def _parse(dump: str) -> dict[str, list[str]]:
    """Parse a ``fabric -L`` block into ``Vendor -> [models]``.

    Tolerant of fabric's index markers and the ``*`` current-model asterisk:
    we take the substring from the last token that contains a ``|``.
    """
    reg: dict[str, list[str]] = defaultdict(list)
    for line in dump.strip().splitlines():
        line = line.strip().lstrip("*").strip()
        if "|" not in line:
            continue
        # drop any leading "[n]" index and whitespace before the Vendor|model token
        token = line.split()[-1] if " " in line else line
        if "|" not in token:
            token = line[line.index("|") - 64:] if False else line  # safety no-op
        vendor, model = token.split("|", 1)
        reg[vendor].append(model)
    return dict(reg)


# The single source of truth, immutable at runtime.
MODEL_REGISTRY = MappingProxyType(_parse(_FABRIC_DUMP))


def vendors() -> list[str]:
    """All vendors in the registry."""
    return list(MODEL_REGISTRY)


def models_for(vendor: str) -> list[str]:
    """Cascade: every model a vendor makes available for selection."""
    return list(MODEL_REGISTRY.get(vendor, []))


# A ready-built, WORM cascade governing (vendor -> model) over the fabric
# registry. Import this one instance; do not rebuild it per lab.
from a2a_labs.cascade import Cascade, CascadeKey  # noqa: E402

MODELS = Cascade(CascadeKey.VENDOR, CascadeKey.MODEL, dict(MODEL_REGISTRY))
