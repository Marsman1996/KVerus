from pathlib import Path
from loguru import logger
from typing import Optional
from abc import ABC, abstractmethod

from .triager import ErrorTriager, ErrorType


class ErrorRefineAgent(ABC):
    """Abstract base class for error refinement agents."""

    @property
    @abstractmethod
    def hints(self) -> str:
        return "Focus on loop invariants and termination conditions."

    @abstractmethod
    def can_handle(self, error_type: ErrorType) -> bool:
        """Check if this agent can handle the given error type."""
        pass

    @abstractmethod
    def refine_error(self, verus_code: str, err_msg: str) -> str:
        """Refine the error message and provide guidance."""
        pass


class LoopErrorAgent(ErrorRefineAgent):
    """Agent specialized in handling loop-related verification errors."""

    def __init__(self, doc_dir: Optional[Path] = None):
        self.doc_dir = doc_dir

    @property
    def hints(self) -> str:
        guidance = ""
        # Add documentation if available
        if self.doc_dir and (self.doc_dir / "while.md").exists():
            guidance += "### Loop Error Refinement:\n"
            guidance += (self.doc_dir / "while.md").read_text(encoding="utf-8")
        return guidance

    def can_handle(self, error_type: ErrorType) -> bool:
        return bool(error_type & ErrorType.LOOP)

    def refine_error(self, verus_code: str, err_msg: str) -> str:
        logger.debug("Processing loop-related error")
        return self.hints


class InvariantErrorAgent(ErrorRefineAgent):
    """Agent specialized in handling invariant-related verification errors."""

    @property
    def hints(self) -> str:
        guidance = "### Invariant Error Refinement:\n"
        guidance += """
1. Invariant Verification Guidelines:
   - Do NOT analyze execution semantics, assume code logic is correct
   - Focus on mathematical properties that must hold
   - Check for conflicts between multiple invariants
   
2. Common Invariant Issues:
   - Boundary conditions: ensure invariants match actual loop bounds
   - Type consistency: verify all variables have correct types
   - Logical consistency: ensure invariants don't contradict each other
   
3. Debugging Steps:
   - Check initialization: invariant must hold before first iteration
   - Check preservation: if invariant holds at start of iteration, it must hold at end
   - Check termination: invariant + negated loop condition should imply postcondition
   
4. Boundary-Specific Issues:
   - If loop goes from 0 to N-1, invariant should use i < N, not i <= N
   - Array access bounds: ensure i < array.len() in invariants
   - Off-by-one errors: carefully check <= vs < conditions
"""
        return guidance

    def can_handle(self, error_type: ErrorType) -> bool:
        return bool(error_type & ErrorType.INV)

    def refine_error(self, verus_code: str, err_msg: str) -> str:
        logger.debug("Processing invariant-related error")

        return self.hints


class TypeErrorAgent(ErrorRefineAgent):
    """Agent for type-related errors."""

    @property
    def hints(self) -> str:
        guidance = "### Type Error Refinement:\n"

        guidance += """
1. Type Annotations:
   - Add explicit type annotations where needed
   - Use `as` for type conversions
   - Verify generic type parameters
   
2. Verus-Specific Types:
   - Use `@` for specification views: `v@` instead of `v.view()`
   - Distinguish exec vs spec types
   - Use appropriate integer types (nat, int vs u32, usize)
   
3. Common Type Issues:
   - spec vs exec mode mismatches
   - Missing trait implementations
   - Incorrect generic constraints
   
4. Example Fixes:
   ```rust
   // Use specification view
   let len: nat = v@.len();
   
   // Explicit type conversion
   let idx = i as usize;
   
   // Generic constraints
   fn foo<T: Clone + PartialEq>(x: T) -> T { ... }
   ```
"""
        return guidance

    def can_handle(self, error_type: ErrorType) -> bool:
        return bool(error_type & ErrorType.VARTYPE)

    def refine_error(self, verus_code: str, err_msg: str) -> str:
        logger.debug("Processing type error")
        return self.hints


class GeneralErrorAgent(ErrorRefineAgent):
    """Agent for handling general/other verification errors."""

    @property
    def hints(self) -> str:
        return ""

    def can_handle(self, error_type: ErrorType) -> bool:
        return bool(error_type & ErrorType.OTHER) or error_type == ErrorType(0)

    def refine_error(self, verus_code: str, err_msg: str) -> str:
        return self.hints
        # logger.debug("Processing general verification error")
        # guidance = "### General Error Refinement:\n"
        # return guidance


class ErrorAgentManager:
    """Manager for coordinating different error refinement agents."""

    def __init__(self, doc_dir: Optional[Path] = None):
        self.agents = [
            LoopErrorAgent(doc_dir),
            InvariantErrorAgent(),
            GeneralErrorAgent(),
            TypeErrorAgent(),
        ]
        # Add more specialized agents
        self.specialized_agents = [
            # TypeErrorAgent(),
            # OwnershipErrorAgent(),
        ]
        # Combine all agents
        self.all_agents = self.agents + self.specialized_agents

    def refine_error(self, verus_code: str, err_msg: str) -> str:
        """Refine error using appropriate agent(s)."""
        triage = ErrorTriager(verus_code, err_msg)
        error_type = triage.get_error_type()

        guidance_parts = []
        used_agents = []

        # Then try general type-based agents
        for agent in self.agents:
            if agent.can_handle(error_type):
                agent_guidance = agent.refine_error(verus_code, err_msg)
                guidance_parts.append(agent_guidance)
                used_agents.append(type(agent).__name__)

        # If no specific agents found, use general agent
        if not guidance_parts:
            general_agent = GeneralErrorAgent()
            guidance_parts.append(general_agent.refine_error(verus_code, err_msg))
            used_agents.append("GeneralErrorAgent")

        # Add agent info at the end
        agent_info = f"\n\n--- Applied Agents: {', '.join(used_agents)} ---"

        return "\n\n".join(guidance_parts)

    def get_available_agents(self) -> list[str]:
        """Get list of available agent names."""
        return [type(agent).__name__ for agent in self.all_agents]

    def get_agent_by_name(self, name: str) -> ErrorRefineAgent:
        """Get a specific agent by name."""
        for agent in self.all_agents:
            if type(agent).__name__ == name:
                return agent
        raise ValueError(f"Agent {name} not found")


class OwnershipErrorAgent(ErrorRefineAgent):
    """Specialized agent for ownership and borrowing errors."""

    @property
    def hints(self) -> str:
        guidance = "### Ownership Error (Specialized):\n"

        guidance += """
1. Borrowing Rules:
   - Only one mutable reference OR multiple immutable references
   - References must be valid for their entire lifetime
   - Cannot move out of borrowed content
   
2. Verus Ownership:
   - Use `&` for immutable references
   - Use `&mut` for mutable references
   - Consider using `tracked` for proof-only data
   
3. Common Solutions:
   - Clone data when ownership transfer needed
   - Use references instead of moving values
   - Restructure code to avoid conflicting borrows
   
4. Example Fixes:
   ```rust
   // Instead of moving
   let result = process(data);
   
   // Use reference
   let result = process(&data);
   
   // Or clone if needed
   let result = process(data.clone());
   ```
"""
        return guidance

    def can_handle(self, error_type: ErrorType) -> bool:
        return True  # Ownership errors can occur in any context

    def can_handle_message(self, err_msg: str) -> bool:
        ownership_keywords = [
            "borrow",
            "ownership",
            "moved",
            "lifetime",
            "reference",
            "mutable",
        ]
        return any(keyword in err_msg.lower() for keyword in ownership_keywords)

    def refine_error(self, verus_code: str, err_msg: str) -> str:
        logger.debug("Processing ownership error")
        return self.hints


class VerusErrorRefiner:
    def __init__(self, doc_dir: Path):
        if not doc_dir.exists():
            logger.warning(
                f"Doc directory {doc_dir} does not exist, skip doc collector."
            )
            logger.warning("Please generate doc first for Verus.")
            self.doc_dir = None
        else:
            self.doc_dir = doc_dir

        # Initialize the agent manager
        self.agent_manager = ErrorAgentManager(self.doc_dir)

    def refine_error(self, verus_code: str, err_msg: str) -> str:
        """Main method for error refinement - delegates to agent manager."""
        return self.agent_manager.refine_error(verus_code, err_msg)
