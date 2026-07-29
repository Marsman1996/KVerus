use vstd::math::abs;
use vstd::prelude::*;
use vstd::slice::*;

verus! {

/// Because Verus doesn't support floating point, we need to use integers instead.
fn has_close_elements(numbers: &[i64], threshold: i64) -> (result: bool)
    ensures
        result == exists|i: int, j: int|
            0 <= i < j < numbers@.len() && abs(numbers[i] - numbers[j]) < threshold,
{
    // If `threshold <= 0`, there can't be any elements closer than `threshold`, so we can
    // just return `false`.
    if threshold <= 0 {
        assert(forall|i: int, j: int|
            0 <= i < j < numbers@.len() ==> abs(numbers[i] - numbers[j]) >= 0 >= threshold);
        return false;
    }
    // Now that we know `threshold > 0`, we can safely compute `i64::MAX - threshold` without
    // risk of overflow. (Subtracting a negative threshold would overflow.)

    let max_minus_threshold: i64 = i64::MAX - threshold;
    let numbers_len: usize = numbers.len();
    for x in 0..numbers_len
        invariant
            max_minus_threshold == i64::MAX - threshold,
            numbers_len == numbers@.len(),
            forall|i: int, j: int|
                0 <= i < j < numbers@.len() && i < x ==> abs(numbers[i] - numbers[j]) >= threshold,
    {
        let numbers_x: i64 = *slice_index_get(numbers, x);  // Verus doesn't yet support `numbers[x]` in exec mode.
        for y in x + 1..numbers_len
            invariant
                max_minus_threshold == i64::MAX - threshold,
                numbers_len == numbers@.len(),
                x < numbers@.len(),
                numbers_x == numbers[x as int],
                forall|i: int, j: int|
                    0 <= i < j < numbers@.len() && i < x ==> abs(numbers[i] - numbers[j])
                        >= threshold,
                forall|j: int| x < j < y ==> abs(numbers_x - numbers[j]) >= threshold,
        {
            let numbers_y = *slice_index_get(numbers, y);  // Verus doesn't yet support `numbers[y]` in exec mode.
            if numbers_x > numbers_y {
                // We have to be careful to avoid overflow. For instance, we
                // can't just check whether `numbers_x - numbers_y < threshold`
                // because `numbers_x - numbers_y` might overflow an `i64`.
                if numbers_y > max_minus_threshold {
                    return true;
                }
                if numbers_x < numbers_y + threshold {
                    return true;
                }
            } else {
                if numbers_x > max_minus_threshold {
                    return true;
                }
                if numbers_y < numbers_x + threshold {
                    return true;
                }
            }
        }
    }
    false
}

} // verus!

fn main() {}
