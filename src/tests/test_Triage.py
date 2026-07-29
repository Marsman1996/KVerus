from loguru import logger

from src.refiner.triager import ErrorTriager, ErrorType


VERUS_CODE = """
fn main() {
    let N: int = 10;
    let mut a: [int; N] = [0; N];
    let mut i: int = 0;
    while i < N {
        invariant 0 <= i <= N;
        invariant forall|j: int| 0 <= j < i ==> a[j] == 1;
        a[i] = 1;
        i = i + 1;
    }
    assert(forall|j: int| 0 <= j < N ==> a[j] == 1);
}"""
ERR_MSG = """
error: invariant not satisfied at end of loop body
  --> /kverus/database/Verus-Bench/code/benchmarks/Diffy/unverified/s42if.rs:37:4
   |
37 |             forall|j: int| 0 <= j < N ==> a[j] == 1,
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""


def run():
    triager = ErrorTriager(VERUS_CODE, ERR_MSG)
    assert triager.has_error_type(ErrorType.LOOP)
    assert triager.has_error_type(ErrorType.INV)
    assert not triager.has_error_type(ErrorType.OTHER)
    logger.debug(f"Is Loop? {triager.is_loop_error()}")
    logger.debug(f"Is Invariant? {triager.is_invariant_error()}")
    logger.debug(f"Is Other? {triager.is_other_error()}")

    triager = ErrorTriager("", "some other error")
    assert not triager.has_error_type(ErrorType.LOOP)
    assert not triager.has_error_type(ErrorType.INV)
    assert triager.has_error_type(ErrorType.OTHER)
    logger.debug(f"Is Other? {triager.is_other_error()}")
