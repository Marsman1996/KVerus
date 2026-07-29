"""
Example usage of the error refinement agents.
"""

from pathlib import Path
from src.refiner.refine_agents import ErrorAgentManager

doc_dir = Path("database/vostd/out/vstd/comprehender/docs")
manager = ErrorAgentManager(doc_dir)


def example_loop_error():
    """Example of handling a loop error."""
    verus_code = """
    fn test_loop() {
        let mut i = 0;
        while i < 10 {
            i = i + 1;
        }
    }
    """

    err_msg = "error: loop must have a decreases clause"

    guidance = manager.refine_error(verus_code, err_msg)
    print("Loop Error Guidance:")
    print(guidance)
    print("\n" + "=" * 80 + "\n")


def example_invariant_error():
    """Example of handling an invariant error."""
    verus_code = """
    fn test_array() {
        let mut a = vec![0; 10];
        let mut i = 0;
        while i <= 10
            invariant i <= a.len()
        {
            a[i] = i;
            i = i + 1;
        }
    }
    """

    err_msg = "error: invariant not satisfied at array access boundary"

    guidance = manager.refine_error(verus_code, err_msg)
    print("Invariant Error Guidance:")
    print(guidance)
    print("\n" + "=" * 80 + "\n")


def example_type_error():
    """Example of handling a type error."""
    verus_code = """
    fn test_types(x: u32) -> nat {
        x
    }
    """

    err_msg = "error: expected type nat, found u32"

    guidance = manager.refine_error(verus_code, err_msg)
    print("Type Error Guidance:")
    print(guidance)
    print("\n" + "=" * 80 + "\n")


def example_doc_refiner():
    """Example using the updated VerusErrorRefiner."""

    verus_code = """
    while condition {
        // loop body
    }
    """

    err_msg = "loop must have a decreases clause"

    # Use the new agent-based refinement
    guidance = manager.refine_error(verus_code, err_msg)
    print("Doc Refiner with Agents:")
    print(guidance)


def list_available_agents():
    """List all available agents."""
    agents = manager.get_available_agents()
    print("Available Error Refinement Agents:")
    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent}")


def run():
    print("Error Refinement Agents - Examples\n")

    list_available_agents()
    print("\n" + "=" * 80 + "\n")

    example_loop_error()
    example_invariant_error()
    example_type_error()
    example_doc_refiner()
