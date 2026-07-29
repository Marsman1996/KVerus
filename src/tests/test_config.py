#!/usr/bin/env python3
"""
Config functionality integration test script
Automatically test various functions of the KVerus configuration system
"""

import subprocess
import sys
from pathlib import Path
import json
import os
import shutil


# Test constants
OPENAI_INPUT = "1\n\ngpt-4o\ntest-api-key-123\n0.7\n-1\n30\n3\ny\n"
OLLAMA_INPUT = "3\n\nllama3.2:latest\nlocalhost\n11434\n-1\n30\n3\ny\n"


class ConfigTester:
    def __init__(self):
        self.test_config = Path("test_config.toml")
        self.test_results = []
        self.passed = 0
        self.failed = 0
        # Use virtual environment Python interpreter - cross-platform detection
        self.python_exe = self._find_python_executable()

    def _find_python_executable(self):
        """Find Python executable path in a cross-platform way"""
        # Try to find virtual environment Python first
        current_dir = Path.cwd()

        # Common virtual environment locations
        venv_paths = [current_dir / ".venv", current_dir / "venv", current_dir / "env"]

        for venv_path in venv_paths:
            if venv_path.exists():
                # Check for Windows executable
                if sys.platform == "win32":
                    python_exe = venv_path / "Scripts" / "python.exe"
                    if python_exe.exists():
                        return str(python_exe)
                else:
                    # Unix-like systems
                    python_exe = venv_path / "bin" / "python"
                    if python_exe.exists():
                        return str(python_exe)

        # Fall back to system Python
        python_exe = shutil.which("python") or shutil.which("python3")
        if python_exe:
            return python_exe

        # Last resort - use sys.executable
        return sys.executable

    def _get_test_binary_path(self, binary_name):
        """Get test binary path in a cross-platform way"""
        if sys.platform == "win32":
            return f"{binary_name}.exe"
        else:
            return f"/usr/local/bin/{binary_name}"

    def _get_test_processor_path(self):
        """Get test processor path in a cross-platform way"""
        if sys.platform == "win32":
            return "C:\\path\\to\\PromeX-Verus"
        else:
            return "/path/to/PromeX-Verus"

    def build_cmd(self, *args):
        """Helper method to build command list"""
        return [self.python_exe, "KVerus.py"] + list(args)

    def build_config_cmd(self, *args):
        """Helper method to build config command with configuration path"""
        return self.build_cmd("config", *args, "--config-path", str(self.test_config))

    def build_assign_cmd(self, *args):
        """Helper method to build config assign command with configuration path"""
        return self.build_cmd(
            "config", "assign", "--config-path", str(self.test_config), *args
        )

    def run_command(self, cmd, description="", expect_success=True, input_text=None):
        """Run command and check results"""
        print(f"\nTesting: {description}")
        print(f"Command: {' '.join(cmd)}")
        if input_text:
            print(f"Input: {input_text.strip()}")

        try:
            result = subprocess.run(
                cmd, input=input_text, capture_output=True, text=True, timeout=10
            )

            success = (
                result.returncode == 0 if expect_success else result.returncode != 0
            )

            if success:
                print("PASS")
                self.passed += 1
                status = "PASS"
            else:
                print("FAIL")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"Error output: {result.stderr}")
                self.failed += 1
                status = "FAIL"

            # Show partial output
            if result.stdout and len(result.stdout) < 500:
                print(f"Output: {result.stdout}")
            elif result.stdout:
                print(f"Output (first 200 chars): {result.stdout[:200]}...")

            self.test_results.append(
                {
                    "description": description,
                    "command": " ".join(cmd),
                    "status": status,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "input": input_text,
                }
            )

            return result

        except subprocess.TimeoutExpired:
            print("FAIL - timeout")
            self.failed += 1
            return None
        except Exception as e:
            print(f"FAIL - execution error: {e}")
            self.failed += 1
            return None

    def cleanup(self):
        """Clean up test files"""
        test_files = [
            self.test_config,
            Path("test_simple.toml"),
            Path("test_backup.toml"),
        ]

        for file in test_files:
            try:
                file.unlink(missing_ok=True)
                print(f"Deleted {file}")
            except Exception as e:
                print(f"Cannot delete {file}: {e}")

    def run_tests(self):
        """Run all tests"""
        print("Starting Config functionality integration tests")
        print("=" * 60)

        # Clean up old test files
        self.cleanup()

        # Test 1: Initialize configuration file
        self.run_command(
            self.build_config_cmd("init"),
            "Initialize empty configuration file",
        )

        # Test 2: List LLM configurations (empty)
        self.run_command(
            self.build_config_cmd("llm", "list"),
            "List empty LLM configuration",
        )

        # Test 3: Add OpenAI LLM configuration (interactive)
        self.run_command(
            self.build_config_cmd("llm", "add", "test_openai_interactive"),
            "Interactive OpenAI LLM addition",
            expect_success=True,
            input_text=OPENAI_INPUT,
        )

        # Test 4: Configure LLM using set command
        self.run_command(
            self.build_config_cmd(
                "llm",
                "set",
                "test_openai_interactive",
                "--api-key",
                "test-key-114514",
                "--model",
                "gpt-4o",
                "--temperature",
                "0.7",
            ),
            "Configuration via set command",
        )

        # Test 5: Add Ollama LLM configuration
        self.run_command(
            self.build_config_cmd(
                "llm",
                "set",
                "test_ollama",
                "--host",
                "localhost",
                "--port",
                "11434",
                "--model",
                "llama2",
            ),
            "Add Ollama LLM configuration via set command",
            expect_success=False,
        )

        # Test 5a: Add Ollama LLM configuration (interactive)
        ollama_input = "1\n\ngpt-4o\ntest-api-key-456\n0.7\n-1\n30\n3\ny\n"
        self.run_command(
            self.build_config_cmd(
                "llm",
                "add",
                "test_ollama_interactive",
            ),
            "Interactive Ollama LLM addition",
            expect_success=True,
            input_text=ollama_input,
        )

        # Test 6: List LLM configurations (with content)
        self.run_command(
            self.build_config_cmd(
                "llm",
                "list",
            ),
            "List configured LLMs",
        )

        # Test 6a: Show specific LLM configuration details
        self.run_command(
            self.build_config_cmd(
                "llm",
                "show",
                "test_openai_interactive",
            ),
            "Show OpenAI LLM detailed configuration",
        )

        # Test 6b: Show non-existent LLM configuration
        self.run_command(
            self.build_config_cmd(
                "llm",
                "show",
                "nonexistent_llm",
            ),
            "Show non-existent LLM configuration",
            expect_success=False,
        )

        # Test 7: List LLM configurations in detail
        self.run_command(
            self.build_config_cmd(
                "llm",
                "list",
                "--verbose",
            ),
            "Detailed list of LLM configurations",
        )

        # Test 8: Set default LLM
        self.run_command(
            self.build_assign_cmd(
                "default",
                "test_openai_interactive",
            ),
            "Set default LLM",
        )

        # Test 9: Assign module LLM
        self.run_command(
            self.build_assign_cmd(
                "comprehension",
                "test_ollama_interactive",
            ),
            "Assign LLM to module",
        )

        # Test 10: Set binary path
        test_exe = self._get_test_binary_path("verus")

        self.run_command(
            self.build_assign_cmd(
                "verus",
                test_exe,
            ),
            "Set Verus binary path",
            expect_success=True,
        )  # Should succeed regardless of file existence

        # Test 10a: View assign options
        self.run_command(
            self.build_assign_cmd(
                "options",
            ),
            "View assign options",
        )

        # Test 10b: List current assignments
        self.run_command(
            self.build_assign_cmd(
                "list",
            ),
            "List current LLM and binary assignments",
        )

        # Test 10c: Assign more module LLMs
        self.run_command(
            self.build_assign_cmd(
                "embedding",
                "test_openai_interactive",
            ),
            "Assign LLM to embedding module",
        )

        # Test 10d: Assign prover module LLM
        self.run_command(
            self.build_assign_cmd(
                "prover",
                "test_ollama_interactive",
            ),
            "Assign LLM to prover module",
        )

        # Test 10e: Set verus_processor path
        processor_path = self._get_test_processor_path()
        self.run_command(
            self.build_assign_cmd(
                "verus_processor",
                processor_path,
            ),
            "Set Verus processor binary path",
        )

        # Test 11: Validate configuration file
        self.run_command(
            self.build_config_cmd(
                "validate",
            ),
            "Validate configuration file",
            expect_success=False,
        )

        # Test 12a: Create a test LLM for deletion testing
        test_remove_input = "3\n\nllama3.2:latest\nlocalhost\n11434\n-1\n30\n3\ny\n"
        self.run_command(
            self.build_config_cmd(
                "llm",
                "add",
                "test_remove_llm",
            ),
            "Add LLM for deletion test",
            expect_success=True,
            input_text=test_remove_input,
        )

        # Test 12b: Delete non-existent LLM
        self.run_command(
            self.build_config_cmd(
                "llm",
                "remove",
                "nonexistent_llm",
            ),
            "Delete non-existent LLM",
            expect_success=False,  # Should fail and exit quickly
        )

        # Test 12c: Delete existing LLM (non-default)
        self.run_command(
            self.build_config_cmd(
                "llm",
                "remove",
                "test_remove_llm",
                "--force",
            ),
            "Force delete test LLM",
        )

        # Test 12d: Try to delete LLM in use (without force)
        self.run_command(
            self.build_config_cmd(
                "llm",
                "remove",
                "test_openai_interactive",
            ),
            "Try to delete LLM in use (cancel deletion)",
            expect_success=True,  # User choosing not to delete is a successful operation
            input_text="n\n",  # Choose not to delete
        )

        # Test 12: Test non-existent configuration file
        self.run_command(
            self.build_cmd(
                "config",
                "llm",
                "list",
                "--config-path",
                "nonexistent.toml",
            ),
            "Test non-existent configuration file",
            expect_success=False,
        )

        # Test 13: Force re-initialize
        self.run_command(
            self.build_config_cmd(
                "init",
                "--force",
            ),
            "Force re-initialize configuration file",
        )

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Total tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success rate: {self.passed/(self.passed+self.failed)*100:.1f}%")

        if self.failed > 0:
            print("\nFailed tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['description']}")
                    if result["stderr"]:
                        print(f"    Error: {result['stderr'][:100]}")

        print("\nDetailed results saved to test_results.json")

        # Save detailed results to JSON file
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)


def run():
    tester = ConfigTester()
    try:
        tester.run_tests()
    finally:
        tester.print_summary()
        # Clean up test files
        print("\nCleaning up test files...")
        tester.cleanup()
