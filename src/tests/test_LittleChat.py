"""
Interactive chat test for LLM clients.

This module provides a simple command-line interface for testing LLM clients
with support for both regular and reasoning models.
"""

import sys
from typing import Optional

from loguru import logger

from src import vars as global_vars
from src.utils import setup_llm
from src.llm.llm import LLMChat, ReasoningLLMClient


# ANSI color codes for better output formatting
class Colors:
    GRAY = "\033[90m"
    RESET = "\033[0m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"


def _print_reasoning_response(reasoning: str, response: str) -> None:
    """Print reasoning response with proper formatting."""
    print(f"{Colors.GRAY}{reasoning}{Colors.RESET}\n{response}")


def _print_welcome_message(llm_name: str) -> None:
    """Print welcome message with usage instructions."""
    print(f"{Colors.GREEN}LittleChat - Interactive LLM Testing{Colors.RESET}")
    print(f"Using LLM: {Colors.YELLOW}{llm_name}{Colors.RESET}")
    print("Type your messages and press Enter. Use Ctrl+C to exit.\n")


def _handle_user_input() -> Optional[str]:
    """
    Get user input with proper error handling.

    Returns:
        User input string, or None if user wants to exit.
    """
    try:
        return input("> ")
    except (KeyboardInterrupt, EOFError):
        print(f"\n{Colors.YELLOW}Goodbye!{Colors.RESET}")
        return None


def run(llm_name: Optional[str] = None) -> None:
    """
    Run interactive chat session with the specified LLM.

    Args:
        llm_name: Name of the LLM configuration to use.
                 Must be provided either as parameter or via command line.
    """
    if llm_name is None:
        logger.info("No LLM name provided, use the default LLM.")
        llm_name = global_vars.config["llm"]["default_llm"]

    logger.debug(f"Initializing LLM: {llm_name}")

    try:
        llm_client = setup_llm(llm_name)
        chat = LLMChat(llm_client)
    except Exception as e:
        logger.error(f"Failed to initialize LLM '{llm_name}': {e}")
        sys.exit(1)

    _print_welcome_message(llm_name)

    # Main chat loop
    while True:
        user_input = _handle_user_input()
        if user_input is None:
            break

        # Skip empty inputs
        if not user_input.strip():
            continue

        try:
            if isinstance(llm_client, ReasoningLLMClient):
                response, reasoning = chat.query_reasoning(user_input)
                _print_reasoning_response(reasoning, response)
            else:
                response = chat.query(user_input)
                print(response)
        except Exception as e:
            logger.error(f"Error during LLM query: {e}")
            print(
                f"{Colors.YELLOW}Sorry, an error occurred. Please try again.{Colors.RESET}"
            )
