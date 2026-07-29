from enum import Enum


class VerifyStatus(Enum):
    """
    Enum for Verus state.
    """

    SUCCESS = "success"
    BUILD_ERROR = "build_error"
    VERIFY_ERROR = "verify_error"
    RUST_ERROR = "rust_error"
    TIMEOUT = "timeout"
    FAIL = "fail"


def is_verify_error(err_msg: str) -> bool:
    """
    Check if the status indicates a verify error.

    :param err_msg: The error message.
    :return: True if the status is VERIFY_ERROR, otherwise False.
    """
    if err_msg.find("verification results:") >= 0:
        return True
    else:
        return False
