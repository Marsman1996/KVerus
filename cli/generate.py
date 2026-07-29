"""
Generate a single-file snippet from a dependency log.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import click
from loguru import logger

from src import vars as global_vars
from src.preprocessor.information import InfoRepository
from src.utils import parse_location, setup_default_config


HEADERS = [
    "use core::fmt::Debug;",
    "use std::ops::Range;",
    "use std::sync::{Mutex, OnceLock};",
    "use vstd::prelude::*;",
    "use vstd::raw_ptr::*;",
    "use vstd::layout::*;",
    "use vstd::arithmetic::{logarithm::*, power::*, power2::*, div_mod::*, mul::*};",
    "use vstd::math::*;",
    "use vstd::multiset::*;",
    "use vstd::{set::*, set_lib::*, map_lib::*};",
    "use vstd::bits::*;",
    "use vstd::calc;",
    "use vstd::rwlock::*;",
    "use vstd::simple_pptr::PPtr;",
    "use vstd::cell::PCell;",
    "use vstd::relations::*;",
    "use vstd::map::*;",
]


@dataclass(frozen=True)
class DependencyEntry:
    dep: str
    location: str
    raw_line: str


def _parse_dependency_line(line: str) -> DependencyEntry:
    location = ""
    dep = line.strip()
    if dep.startswith("[") and "]" in dep:
        bracket, rest = dep.split("]", 1)
        location = bracket[1:].strip()
        dep = rest.strip()
    if location.lower() == "location not found":
        location = ""
    return DependencyEntry(dep=dep, location=location, raw_line=line)


def _parse_dependencies(lines: Iterable[str]) -> List[DependencyEntry]:
    entries: List[DependencyEntry] = []
    in_section = False

    for raw_line in lines:
        line = raw_line.strip()
        entries.append(_parse_dependency_line(line))

    return entries


def _parse_log_location(location: str) -> Tuple[Optional[str], int]:
    if not location:
        return None, 0
    parts = location.rsplit(":", 2)
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        return parts[0], int(parts[1])
    if len(parts) >= 2 and parts[-1].isdigit():
        return ":".join(parts[:-1]), int(parts[-1])
    return None, 0


def _iter_infos(info_repo: InfoRepository) -> Iterable[Tuple[str, Iterable[object]]]:
    return (
        ("function", info_repo.function_infos.values()),
        ("composite", info_repo.composite_infos.values()),
        ("typedef", info_repo.typedef_infos.values()),
        ("trait", info_repo.trait_infos.values()),
        ("impl", info_repo.impl_infos.values()),
    )


def resolve_dependency(
    entry: DependencyEntry,
    info_repo: InfoRepository,
) -> Tuple[Optional[Tuple[str, object]], Optional[str]]:
    warning = None
    if not entry.location:
        return None, f"NO_LOCATION\t{entry.dep}"

    file_path, line = _parse_log_location(entry.location)
    if not file_path or line <= 0:
        return None, f"INVALID_LOCATION\t{entry.dep}\t{entry.location}"

    if entry.dep.strip().startswith("impl"):
        matches = _collect_matches(info_repo.impl_infos.values(), file_path, line)
        return _select_match(entry, [("impl", info) for info in matches])

    func_matches = _collect_matches(info_repo.function_infos.values(), file_path, line)
    if func_matches:
        return _select_match(entry, [("function", info) for info in func_matches])

    matches: List[Tuple[str, object]] = []
    for kind, infos in (
        ("impl", info_repo.impl_infos.values()),
        ("trait", info_repo.trait_infos.values()),
        ("composite", info_repo.composite_infos.values()),
        ("typedef", info_repo.typedef_infos.values()),
    ):
        for info in infos:
            if _impl_range_contains(info, file_path, line):
                matches.append((kind, info))

    return _select_match(entry, matches)


def _collect_matches(
    infos: Iterable[object], file_path: str, line: int
) -> List[object]:
    matches: List[object] = []
    for info in infos:
        if _impl_range_contains(info, file_path, line):
            matches.append(info)
    return matches


def _select_match(
    entry: DependencyEntry, matches: List[Tuple[str, object]]
) -> Tuple[Optional[Tuple[str, object]], Optional[str]]:
    if not matches:
        return None, f"NO_MATCH\t{entry.dep}\t{entry.location}"
    if len(matches) == 1:
        return matches[0], None
    locs = [getattr(info, "location", "") for _, info in matches]
    warning = f"MULTIPLE_MATCHES\t{entry.dep}\t{locs}"
    matches = _prefer_kind_order(matches)
    if matches:
        warning += f"\tCHOSEN\t{getattr(matches[0][1], 'location', '')}"
        return matches[0], warning
    return None, warning


def _impl_range_contains(info: object, file_path: str, line: int) -> bool:
    impl_range = getattr(info, "impl_range", None)
    if not impl_range or len(impl_range) != 2:
        return False
    start, end = impl_range
    if start is None or end is None:
        return False
    start_file = Path(getattr(start, "file", ""))
    end_file = Path(getattr(end, "file", ""))
    if not start_file or not end_file:
        return False
    if start_file.resolve() != end_file.resolve():
        return False
    if not _path_matches(start_file, file_path):
        return False
    start_line = getattr(start, "line", 0)
    end_line = getattr(end, "line", 0)
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        return False
    if start_line <= line <= end_line:
        return True
    return False


def _impl_range_span(info: object) -> int:
    impl_range = getattr(info, "impl_range", None)
    if not impl_range or len(impl_range) != 2:
        return 1_000_000_000
    start, end = impl_range
    if start is None or end is None:
        return 1_000_000_000
    start_line = getattr(start, "line", None)
    end_line = getattr(end, "line", None)
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        return 1_000_000_000
    return max(0, end_line - start_line)


def _prefer_kind_order(matches: List[Tuple[str, object]]) -> List[Tuple[str, object]]:
    priority = {
        "impl": 0,
        "trait": 1,
        "composite": 2,
        "function": 3,
        "typedef": 4,
    }
    return sorted(
        matches,
        key=lambda item: (
            priority.get(item[0], 99),
            _impl_range_span(item[1]),
        ),
    )


def _path_matches(source_file: Path, log_path: str) -> bool:
    log_path = log_path.strip()
    if not log_path:
        return False
    source_resolved = source_file.resolve()
    log_path_obj = Path(log_path)
    if log_path_obj.is_absolute():
        try:
            return source_resolved == log_path_obj.resolve()
        except OSError:
            return False
    log_suffix = log_path_obj.as_posix()
    return source_resolved.as_posix().endswith(log_suffix)


def _extract_impl_code(info: object) -> str:
    impl_range = getattr(info, "impl_range", None)
    if not impl_range or len(impl_range) != 2:
        return ""
    start, end = impl_range
    if start is None or end is None:
        return ""
    try:
        return start.get_content_till_pos(end)
    except Exception:
        return ""


def _extract_typedef_code(info: object) -> str:
    definition = getattr(info, "definition", "")
    if isinstance(definition, str):
        return definition.strip()
    return ""


def _append_snippet(
    output_snippets: List[str],
    seen_locations: set[str],
    dep: str,
    info: object,
    tag: str = "",
) -> None:
    location = getattr(info, "location", "")
    if not location or location in seen_locations:
        return
    impl_code = _extract_impl_code(info)
    if not impl_code:
        impl_code = _extract_typedef_code(info)
    if not impl_code:
        return
    seen_locations.add(location)
    if tag:
        header = f"// {dep}\n// {tag}: {location}"
    else:
        header = f"// {dep}\n// {location}"
    output_snippets.append(f"{header}\n{impl_code}\n")


def _append_heldby_snippet(
    output_snippets: List[str],
    seen_locations: set[str],
    dep: str,
    info: object,
) -> bool:
    heldby_impl = getattr(info, "heldby_impl", None)
    heldby_trait = getattr(info, "heldby_trait", None)

    if heldby_impl and hasattr(heldby_impl, "location"):
        location = getattr(heldby_impl, "location", "")
        if location:
            impl_signature = getattr(heldby_impl, "signature", "").strip()
            func_code = _extract_impl_code(info)
            if impl_signature and func_code:
                seen_locations.add(location)
                header = f"// {dep}\n// heldby_impl: {location}"
                wrapped = f"{impl_signature} {{\n{func_code}\n}}"
                output_snippets.append(f"{header}\n{wrapped}\n")
                composite_info = getattr(heldby_impl, "composite_info", None)
                if composite_info is not None:
                    _append_snippet(
                        output_snippets,
                        seen_locations,
                        dep,
                        composite_info,
                        "impl_composite_info",
                    )
                return True
        return False
    if heldby_trait and hasattr(heldby_trait, "location"):
        _append_snippet(
            output_snippets, seen_locations, dep, heldby_trait, "heldby_trait"
        )
        return True
    return False


def _append_used_infos(
    output_snippets: List[str],
    seen_locations: set[str],
    dep: str,
    info: object,
    depth: int = 0,
    max_depth: int = 5,
) -> None:
    if depth >= max_depth:
        return
    for attr, tag in (
        ("used_composites", "used_composite"),
        ("used_typedefs", "used_typedef"),
    ):
        used_list = getattr(info, attr, None)
        if not isinstance(used_list, list):
            continue
        for used_info in used_list:
            if used_info is None:
                continue
            _append_snippet(output_snippets, seen_locations, dep, used_info, tag)
            _append_used_infos(
                output_snippets,
                seen_locations,
                dep,
                used_info,
                depth=depth + 1,
                max_depth=max_depth,
            )


def generate_snippets(
    entries: Iterable[DependencyEntry],
    info_repo: InfoRepository,
) -> List[str]:
    output_snippets: List[str] = []
    seen_locations: set[str] = set()
    entries_list = list(entries)
    if entries_list:
        last_entry = entries_list[-1]
        last_match, _ = resolve_dependency(last_entry, info_repo)
        if last_match:
            last_kind, last_info = last_match
            if last_kind == "function" and getattr(last_info, "is_empty", False):
                logger.warning(
                    "LAST_DEP_EMPTY_FUNCTION\t{}\t{}",
                    last_entry.dep,
                    getattr(last_info, "location", ""),
                )
                return []

    for entry in entries_list:
        match, warning = resolve_dependency(entry, info_repo)
        if warning:
            logger.warning(warning)
        if not match:
            continue
        kind, info = match
        logger.debug(
            "MATCH\t{}\t{}\t{}",
            entry.dep,
            kind,
            getattr(info, "location", ""),
        )
        if kind == "function":
            emitted = _append_heldby_snippet(
                output_snippets, seen_locations, entry.dep, info
            )
            if not emitted:
                _append_snippet(output_snippets, seen_locations, entry.dep, info)
            _append_used_infos(output_snippets, seen_locations, entry.dep, info)
            continue
        _append_snippet(output_snippets, seen_locations, entry.dep, info)
        _append_used_infos(output_snippets, seen_locations, entry.dep, info)

    return output_snippets


@click.command(help="Generate snippet(s) from dependency log(s).")
@click.option(
    "-F",
    "--fvt",
    "fvt_name",
    default=None,
    help="The name of the FVT to use for locating preprocessor outputs.",
)
@click.option(
    "--log-path",
    "log_path",
    required=False,
    type=click.Path(path_type=Path, resolve_path=True, dir_okay=False, file_okay=True),
    help="Path to a single dependency log file.",
)
@click.option(
    "--log-dir",
    "log_dir",
    required=False,
    type=click.Path(path_type=Path, resolve_path=True, dir_okay=True, file_okay=False),
    help="Directory containing dependency log files.",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    required=True,
    type=click.Path(path_type=Path, resolve_path=True, dir_okay=True, file_okay=True),
    help="Output .rs snippet path (file mode) or output directory (dir mode).",
)
@click.option(
    "--info-path",
    "info_path",
    required=False,
    type=click.Path(path_type=Path, resolve_path=True, dir_okay=False, file_okay=True),
    help="Optional path to preprocessor info.pkl.",
)
def generate(
    fvt_name: str,
    log_path: Optional[Path],
    log_dir: Optional[Path],
    output_path: Path,
    info_path: Optional[Path],
) -> None:
    setup_default_config(fvt_name)

    if bool(log_path) == bool(log_dir):
        raise click.ClickException("Provide exactly one of --log-path or --log-dir.")
    if log_path and not log_path.exists():
        raise click.ClickException(f"Log file not found: {log_path}")
    if log_dir and not log_dir.exists():
        raise click.ClickException(f"Log directory not found: {log_dir}")

    if info_path is None:
        info_path = (
            Path(global_vars.fvt_config["output_path"]) / "preprocessor" / "info.pkl"
        )

    try:
        info_repo = InfoRepository.load(info_path)
    except Exception as exc:
        raise click.ClickException(
            f"Failed to load preprocessor info: {info_path} ({exc})"
        )

    def _write_output(out_file: Path, snippets: List[str]) -> None:
        content = "\n".join(snippets)
        headers = "\n".join(HEADERS)
        out_file.write_text(
            f"{headers}\n\nverus! {{\n{content}\n}}\n\nfn main() {{}}",
            encoding="utf-8",
        )

    def _process_log_entry(
        src_log: Path, dst_out: Path, strict_error: bool = False
    ) -> None:
        entries = _parse_dependencies(src_log.read_text(encoding="utf-8").splitlines())
        if not entries:
            msg = f"No dependencies found in log: {src_log}"
            if strict_error:
                raise click.ClickException(msg)
            logger.warning(msg)
            return

        generated_snippets = generate_snippets(entries, info_repo)
        if not generated_snippets:
            msg = (
                "No snippets generated from dependency log."
                if strict_error
                else f"No snippets generated from dependency log: {src_log}"
            )
            if strict_error:
                raise click.ClickException(msg)
            logger.warning(msg)
            return

        dst_out.parent.mkdir(parents=True, exist_ok=True)
        _write_output(dst_out, generated_snippets)
        logger.success(f"Wrote snippet output to {dst_out}")

    if log_path:
        _process_log_entry(log_path, output_path, strict_error=True)
        return

    log_files = sorted(log_dir.glob("*.log")) if log_dir else []
    if not log_files:
        raise click.ClickException(f"No .log files found in {log_dir}")
    output_path.mkdir(parents=True, exist_ok=True)

    for log_file in log_files:
        stem = log_file.stem.replace("::", "-").replace("&", "_").replace("%", "_")
        _process_log_entry(log_file, output_path / f"{stem}.rs")


if __name__ == "__main__":
    generate()
