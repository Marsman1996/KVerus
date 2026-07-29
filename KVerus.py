#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KVerus CLI
"""

import sys
import platform
import tomllib
import click
from pathlib import Path
from loguru import logger
import datetime
import tqdm
import sys

from src import vars as global_vars
from src.utils import normalize_path_input, expand_config_path

SUBCOMMANDS = (
    # add commands here.
    "config",
    "preprocess",
    "comprehend",
    "prove",
    "simplify",
    "eval",
    "generate",
    "test",
)


def setup_subcommands():
    """
    Import command-line module and add the right command.
    Optimized selective loading for better performance.
    """
    # Command configuration - more efficient with frozensets for O(1) lookups
    LIGHTWEIGHT_COMMANDS = frozenset(["config"])
    HEAVY_COMMANDS = frozenset(
        [
            "preprocess",
            "comprehend",
            "prove",
            "simplify",
            "eval",
            "generate",
            "test",
        ]
    )

    # Early exit optimization - check if we need to load anything at all
    user_command = get_command_from_argv()
    is_help_request = any(arg in ("--help", "-h") for arg in sys.argv)
    is_no_command = len(sys.argv) == 1

    # Determine minimal set of commands to load
    if is_no_command or is_help_request:
        # Load all commands for help display
        commands_to_load = LIGHTWEIGHT_COMMANDS | HEAVY_COMMANDS
    elif user_command in LIGHTWEIGHT_COMMANDS:
        # Only load the lightweight command
        commands_to_load = {user_command}
    elif user_command in HEAVY_COMMANDS:
        # Load lightweight commands + specific heavy command
        commands_to_load = LIGHTWEIGHT_COMMANDS | {user_command}
    else:
        # Unknown command - load lightweight commands only (for error handling)
        commands_to_load = LIGHTWEIGHT_COMMANDS

    # Batch load commands with improved error handling
    failed_commands = []
    for cmd in commands_to_load:
        if not _load_single_command(cmd):
            failed_commands.append(cmd)

    # Report failures in batch (reduces logging overhead)
    if failed_commands:
        logger.warning(f"Failed to load commands: {', '.join(failed_commands)}")


def _load_single_command(cmd: str) -> bool:
    """
    Load a single command module efficiently.

    :param cmd: Command name to load
    :return: True if successful, False otherwise
    """
    module = __import__(f"cli.{cmd}", fromlist=[cmd])
    command_func = getattr(module, cmd)
    butler.add_command(command_func)
    return True


def setup_logger(debug: bool):
    """
    Setup logging level.

    :param debug: If True, set the logging level to DEBUG.
    """
    logger.remove()
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sink=tqdm.tqdm.write,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <magenta>{thread.name}</magenta> <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        colorize=True,
    )
    Path("logs").mkdir(exist_ok=True)
    cmd_str = "_".join(sys.argv).replace(" ", "_").replace("\\", "/").replace("/", "_")
    log_filename = (
        f"logs/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{cmd_str}.log"
    )
    if len(log_filename) > 255:
        log_filename = log_filename[:200] + ".log"
    logger.add(
        str(log_filename),
        level=level,
        enqueue=True,
        format="{time} | {thread.name} {level} | {name}:{function}:{line} | {message}",
        colorize=False,
    )
    logger.info(
        f"Logger set up with level {level}, log will be saved to {log_filename}"
    )


def get_command_from_argv():
    """
    Extract the actual command name from sys.argv, handling Click options properly.
    Returns the command name or None if not found.
    """
    if len(sys.argv) <= 1:
        return None

    # Skip global options and find the actual command
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            # Check exact match
            if arg in SUBCOMMANDS:
                return arg
            # Check normalized match (hyphen to underscore)
            normalized_arg = arg.replace("-", "_")
            if normalized_arg in SUBCOMMANDS:
                return normalized_arg
    return None


def load_config(config_path: Path, fvt_cfg_path: Path):
    """
    Load the config.toml and libraries.toml

    :param config_path: The path to the KVerus config file.
    :param library_path: The path to the fvt config file.
    """
    try:
        # Check if config file exists
        if not config_path.exists():
            # For config init/setup command, we don't need to load config
            # Use more robust command detection
            command = get_command_from_argv()
            is_config_init_command = (
                command == "config"
                and len(sys.argv) >= 3
                and any(arg in ["init", "setup"] for arg in sys.argv[2:])
            )

            if is_config_init_command:
                global_vars.config = {}
                global_vars.config_template = {}
                global_vars.fvts = {}
                return
            else:
                logger.error(f"Configuration file not found: {config_path}")
                logger.info(
                    "Run 'kverus config init/setup' to create a configuration file"
                )
                sys.exit(1)

        def normalize_toml_paths(text):
            return text.replace("\\", "/")

        config_text = config_path.read_text(encoding="utf-8")
        config_text = normalize_toml_paths(config_text)
        global_vars.config = tomllib.loads(config_text)

        config_template_text = (
            Path(__file__).resolve().parent / "config.template.toml"
        ).read_text(encoding="utf-8")
        config_template_text = normalize_toml_paths(config_template_text)
        global_vars.config_template = tomllib.loads(config_template_text)

        fvts_text = fvt_cfg_path.read_text(encoding="utf-8")
        fvts_text = normalize_toml_paths(fvts_text)
        global_vars.fvts = tomllib.loads(fvts_text)

        fvts_template_text = (
            Path(__file__).resolve().parent / "fvts.template.toml"
        ).read_text(encoding="utf-8")
        fvts_template_text = normalize_toml_paths(fvts_template_text)
        global_vars.fvts_template = tomllib.loads(fvts_template_text)
    except Exception as e:
        logger.critical(f"Toml load error when loading config: {e}")
        sys.exit(1)

    global_vars.kverus_path = Path(Path(__file__).resolve().parent.as_posix())

    def _set_bin_path(bin_name):
        """
        Because the path of the preprocessor binary may be relative to the KVerus path,
        we need to set the path of the preprocessor binary here.
        """
        bin_path = global_vars.config.get(
            "paths", global_vars.config_template["paths"]
        ).get(bin_name, global_vars.config_template["paths"][bin_name])
        bin_path = normalize_path_input(bin_path)
        bin_path = expand_config_path(bin_path)

        if platform.system() == "Windows" and not bin_path.endswith(".exe"):
            bin_path += ".exe"

        global_vars.config.setdefault("paths", dict())[bin_name] = bin_path

    _set_bin_path("verus_processor")


@click.group()
@click.option("-D", "is_debug", help="Output debug information.", flag_value=True)
@click.option(
    "--config",
    "config",
    help="Specify the config file.",
    type=click.Path(dir_okay=False, path_type=Path),
    default=str(Path(__file__).resolve().parent / "config.toml"),
)
@click.option(
    "-F",
    "--fvt-config",
    "fvt_config",
    help="Specify the formal verify target config file.",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=str(Path(__file__).resolve().parent / "fvts.template.toml"),
)
def butler(
    is_debug: bool,
    config: Path,
    fvt_config: Path,
):
    """KVerus CLI"""
    setup_logger(is_debug)
    load_config(config, fvt_config)


def main():
    setup_subcommands()
    butler()


if __name__ == "__main__":
    main()
