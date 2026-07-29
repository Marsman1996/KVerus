"""
Triage the verification errors
"""

from enum import IntFlag, auto


class ErrorType(IntFlag):
    LOOP = auto()
    INV = auto()
    """invariant"""
    VARTYPE = auto()
    OTHER = auto()


class ErrorTriager:
    """
    Class to triage verification errors and classify them by type.

    Supports bitwise operations for combining error types.
    """

    def __init__(self, verus_code: str, err_msg: str) -> None:
        self.verus_code = verus_code
        self.err_msg = err_msg
        self.error_type = self._triage()

    def get_error_type(self) -> ErrorType:
        """Get the classified error type."""
        return self.error_type

    def has_error_type(self, error_type: ErrorType) -> bool:
        """Check if the error has the specified type(s)."""
        return bool(self.error_type & error_type)

    def is_loop_error(self) -> bool:
        return bool(self.error_type & ErrorType.LOOP)

    def is_invariant_error(self) -> bool:
        return bool(self.error_type & ErrorType.INV)

    def is_other_error(self) -> bool:
        return bool(self.error_type & ErrorType.OTHER)

    @staticmethod
    def _is_related_to_loop(verus_code: str, err_msg: str) -> bool:
        """
        Check if the Verus code is related to loop
        FIXME: this is a very naive implementation
        """
        loop_keywords = ("while",)
        return any(keyword in verus_code for keyword in loop_keywords)

    @staticmethod
    def _is_related_to_invariant(verus_code: str, err_msg: str) -> bool:
        """
        Check if the Verus code is related to invariant
        """
        invariant_indicators = ("invariant not satisfied",)
        return any(indicator in err_msg for indicator in invariant_indicators)

    @staticmethod
    def _is_related_to_vartype(verus_code: str, err_msg: str) -> bool:
        """
        Check if the Verus code is related to variable type mismatch
        """
        vartype_indicators = (
            "mismatched types",
            "error: The Verus types",
        )
        return any(indicator in err_msg for indicator in vartype_indicators)

    def _triage(self) -> ErrorType:
        """
        Triage the verification errors
        """
        error_type = ErrorType(0)

        if self._is_related_to_invariant(self.verus_code, self.err_msg):
            error_type |= ErrorType.INV
        if self._is_related_to_vartype(self.verus_code, self.err_msg):
            error_type |= ErrorType.VARTYPE

        # FIXME: currently we only consider loop if no other type is detected
        if error_type == ErrorType(0) and self._is_related_to_loop(
            self.verus_code, self.err_msg
        ):
            error_type |= ErrorType.LOOP

        return error_type if error_type else ErrorType.OTHER
