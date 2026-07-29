"""Generate refiner-friendly hint markdown files from documentation with an LLM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import re
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from loguru import logger

from src.llm.llm import LLMClient


@dataclass
class RefineHintSummary:
    """Structured hint summary for refine agents."""

    generated_at: str
    fvt_name: str
    model: str
    sources: list[str]
    hints: dict[str, str]

    def dump_markdown_files(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        for key, markdown in self.hints.items():
            (output_dir / f"{key}.md").write_text(markdown + "\n", encoding="utf-8")


class RefineHintSummarizer:
    """Summarize documentation into error-refinement hints."""

    MAX_DOC_CHARS = 6000
    MAX_TOTAL_CHARS = 24000
    SUPPORTED_SUFFIXES = {".md", ".txt", ".html", ".htm", ".adoc", ".rst"}
    KEYWORD_NAMES = {"README", "readme", "USAGE", "usage"}
    REQUIRED_KEYS = ("loop", "invariant", "vartype", "other")
    KEY_DOC_BINDINGS = {
        "loop": [
            "database/CortenMM/code/tools/verus/source/docs/guide/src/while.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/break.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/exec_termination.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/recursion_loops.md",
        ],
        "invariant": [
            "database/CortenMM/code/tools/verus/source/docs/guide/src/while.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/invariants.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/binary_search.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/break.md",
        ],
        "vartype": [
            "database/CortenMM/code/tools/verus/source/docs/guide/src/pervasive.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/integers.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/reference-as.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/reference-exec-signature.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/exec_spec.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/container_bst_clone.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/equality.md",
            "database/CortenMM/code/tools/verus/source/docs/guide/src/reference-global.md",
        ],
    }
    DEFAULT_BOUND_DOC_SOURCES = tuple(
        dict.fromkeys(
            bound_path
            for bound_paths in KEY_DOC_BINDINGS.values()
            for bound_path in bound_paths
        )
    )

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def summarize_from_config(
        self,
        *,
        fvt_name: str,
        document_paths: list[str],
        exclude_paths: list[str] | None,
        output_dir: Path,
    ) -> RefineHintSummary:
        """Resolve configured documents, summarize them, and dump markdown files."""
        if not document_paths:
            raise ValueError(
                "No document_paths configured for refinement hint summary."
            )

        resolved_sources = self._resolve_document_sources(
            document_paths,
            [Path(path) for path in (exclude_paths or [])],
        )
        if not resolved_sources:
            raise ValueError(
                "No documentation sources were resolved for summary generation."
            )

        docs = self._load_documents(resolved_sources)
        if not docs:
            raise ValueError(
                "No readable documentation content found for summary generation."
            )

        hints = self._summarize_required_keys(docs)
        summary = RefineHintSummary(
            generated_at=datetime.now(timezone.utc).isoformat(),
            fvt_name=fvt_name,
            model=getattr(self.llm_client, "model", self.llm_client.__class__.__name__),
            sources=[
                source if isinstance(source, str) else str(source)
                for source in resolved_sources
            ],
            hints=hints,
        )
        summary.dump_markdown_files(output_dir)
        logger.success(f"Refinement hint markdown files written to {output_dir}")
        return summary

    def _summarize_required_keys(self, docs: list[dict[str, str]]) -> dict[str, str]:
        bound_docs, general_docs = self._group_docs_for_hint_keys(docs)
        hints: dict[str, str] = {}
        for key in self.REQUIRED_KEYS:
            response = self.llm_client.query_once(
                user_prompt=self._build_user_prompt_for_key(
                    key,
                    bound_docs.get(key, []),
                    general_docs,
                ),
                system_prompt=self._system_prompt_for_key(key),
            )
            if not response or not response.strip():
                raise ValueError(
                    f"Empty LLM response while generating {key} refinement hint."
                )
            hints[key] = self._normalize_markdown_response(response, key)
        return hints

    @classmethod
    def _resolve_document_sources(
        cls,
        document_paths: list[str],
        exclude_paths: list[Path],
    ) -> list[str | Path]:
        sources: list[str | Path] = []
        seen_sources: set[str] = set()

        def add_source(source: str | Path):
            normalized = str(source if isinstance(source, str) else source.resolve())
            if normalized in seen_sources:
                return
            seen_sources.add(normalized)
            sources.append(source)

        for raw_path in [*document_paths, *cls.DEFAULT_BOUND_DOC_SOURCES]:
            if cls._is_url(raw_path):
                add_source(raw_path)
                continue

            path = Path(raw_path)
            if path.is_file():
                if not cls._is_supported_file(path):
                    logger.warning(f"Skipping unsupported document file {path}")
                    continue
                if cls._path_in_paths(path, exclude_paths):
                    continue
                add_source(path.resolve())
                continue

            if path.is_dir():
                for file_path in sorted(path.rglob("*")):
                    if not file_path.is_file() or not cls._is_supported_file(file_path):
                        continue
                    if cls._path_in_paths(file_path, exclude_paths):
                        continue
                    add_source(file_path.resolve())
                continue

            logger.warning(f"Document path {path} is not a file, directory, or URL")

        return sources

    @classmethod
    def _is_supported_file(cls, path: Path) -> bool:
        return (
            path.suffix.lower() in cls.SUPPORTED_SUFFIXES
            or path.name in cls.KEYWORD_NAMES
        )

    @staticmethod
    def _path_in_paths(path: Path, candidates: list[Path]) -> bool:
        try:
            resolved = path.resolve()
        except FileNotFoundError:
            resolved = path
        for candidate in candidates:
            try:
                resolved_candidate = candidate.resolve()
            except FileNotFoundError:
                resolved_candidate = candidate
            if resolved == resolved_candidate or resolved_candidate in resolved.parents:
                return True
        return False

    @staticmethod
    def _is_url(path: str) -> bool:
        parsed = urlparse(path)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _load_documents(self, sources: list[str | Path]) -> list[dict[str, str]]:
        docs: list[dict[str, str]] = []
        remaining_chars = self.MAX_TOTAL_CHARS
        for source in sources:
            if remaining_chars <= 0:
                break
            text = self._read_source(source)
            if not text:
                continue

            trimmed = text[: min(self.MAX_DOC_CHARS, remaining_chars)].strip()
            if not trimmed:
                continue
            docs.append(
                {
                    "source": str(source),
                    "content": trimmed,
                }
            )
            remaining_chars -= len(trimmed)
        return docs

    def _read_source(self, source: str | Path) -> str:
        if isinstance(source, Path):
            return self._read_file(source)
        return self._read_url(source)

    @staticmethod
    def _read_file(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            logger.warning(f"Failed to read document {path}: {exc}")
            return ""

    @staticmethod
    def _read_url(url: str) -> str:
        try:
            with urlopen(url, timeout=20) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                raw = response.read().decode(charset, errors="ignore")
        except (OSError, URLError) as exc:
            logger.warning(f"Failed to fetch document URL {url}: {exc}")
            return ""

        # Strip scripts/styles/tags to provide compact readable content.
        no_script = re.sub(
            r"<script.*?</script>", " ", raw, flags=re.IGNORECASE | re.DOTALL
        )
        no_style = re.sub(
            r"<style.*?</style>", " ", no_script, flags=re.IGNORECASE | re.DOTALL
        )
        text = re.sub(r"<[^>]+>", " ", no_style)
        text = unescape(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _system_prompt_for_key(key: str) -> str:
        title = f"### {key.capitalize()} Error Refinement:"
        return (
            "You are an expert in Verus verification and documentation distillation. "
            "Your job is to convert documentation into short, practical refinement hints "
            "that can be embedded directly in a Python error-refinement agent. "
            "Use only information supported by the provided documents. "
            "Do not analyze specific program execution semantics. "
            "Return markdown only, with no code fences around the whole response. "
            f"Start the response with exactly '{title}'."
        )

    def _build_user_prompt_for_key(
        self,
        key: str,
        bound_docs: list[dict[str, str]],
        general_docs: list[dict[str, str]],
    ) -> str:
        sections = []
        if bound_docs:
            sections.append(
                self._format_doc_section(
                    f"{key.capitalize()}-bound documents",
                    bound_docs,
                )
            )
        sections.append(self._format_doc_section("General documents", general_docs))

        key_instructions = {
            "loop": (
                "Focus on loop proof obligations, maintenance of loop facts, exit reasoning, and break-specific caveats when supported."
            ),
            "invariant": (
                "Include sections covering verification guidelines, common issues, debugging steps, and boundary-specific issues when the docs support them."
            ),
            "vartype": (
                "Focus on spec versus exec mode, integer type selection, casts with as, @ view usage, and trait or generic constraints only when supported by the docs."
            ),
            "other": (
                "Provide conservative, high-signal general verification guidance supported by the docs without inventing narrow rules."
            ),
        }

        return (
            f"Summarize the documentation below into reusable {key} error-refinement hints for KVerus.\n"
            "Requirements:\n"
            "1. Return markdown only.\n"
            f"2. Start with '### {key.capitalize()} Error Refinement:'.\n"
            "3. Keep the output concise but actionable.\n"
            "4. Use numbered sections with bullet points when appropriate.\n"
            "5. If key-bound documents are provided below, treat them as the authoritative source for this key and use general documents only as secondary support.\n"
            "6. If the docs do not strongly support a claim, keep the advice conservative.\n"
            "7. Do not mention missing evidence or cite document numbers inside the hint text.\n"
            f"8. {key_instructions[key]}\n\n"
            f"{'\n\n'.join(sections)}"
        )

    @classmethod
    def _group_docs_for_hint_keys(
        cls, docs: list[dict[str, str]]
    ) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, str]]]:
        bound_docs: dict[str, list[dict[str, str]]] = {
            key: [] for key in cls.KEY_DOC_BINDINGS
        }
        general_docs: list[dict[str, str]] = []

        for doc in docs:
            matched = False
            for key, bound_paths in cls.KEY_DOC_BINDINGS.items():
                if any(
                    cls._matches_bound_doc(doc["source"], bound_path)
                    for bound_path in bound_paths
                ):
                    bound_docs[key].append(doc)
                    matched = True
            if not matched:
                general_docs.append(doc)

        return bound_docs, general_docs

    @staticmethod
    def _matches_bound_doc(source: str, bound_path: str) -> bool:
        normalized_source = source.replace("\\", "/")
        normalized_bound = bound_path.replace("\\", "/")
        return normalized_source.endswith(normalized_bound)

    @staticmethod
    def _format_doc_section(title: str, docs: list[dict[str, str]]) -> str:
        lines = [f"{title}:"]
        if not docs:
            lines.append("(none)")
            return "\n".join(lines)

        for index, doc in enumerate(docs, start=1):
            lines.append(f"[Document {index}] Source: {doc['source']}")
            lines.append(doc["content"])
            lines.append("")

        return "\n".join(lines).rstrip()

    @staticmethod
    def _normalize_markdown_response(response: str, key: str) -> str:
        cleaned = response.strip()
        fenced_match = re.search(
            r"```(?:md|markdown)?\s*(.*?)\s*```", cleaned, re.DOTALL
        )
        if fenced_match:
            cleaned = fenced_match.group(1).strip()

        expected_heading = f"### {key.capitalize()} Error Refinement:"
        if not cleaned.startswith(expected_heading):
            cleaned = f"{expected_heading}\n\n{cleaned}"
        return cleaned
