#[allow(unused_imports)]
use vstd::prelude::*;

fn main() {}

verus! {
fn linear_search(nums: Vec<i32>, target: i32) -> (ret: i32)
requires
    nums@.len() < 0x8000_0000,
ensures
    ret < nums@.len(),
    ret >=0 ==> nums@[ret as int] == target,
    ret >=0 ==> forall |i: int| 0 <= i < ret as int ==> #[trigger]nums@[i]!= target,
    ret < 0 ==> forall |i: int| 0 <= i < nums@.len() as int ==> #[trigger]nums@[i] != target,
{
    let mut i = 0;
    while i < nums.len()
    invariant
        i <= nums.len(),
        forall |j: int| 0 <= j < i as int ==> #[trigger]nums@[j] != target,
        nums@.len() < 0x8000_0000,
    decreases
        nums.len() - i,
    {
        if nums[i] == target {
            return i as i32;
        }
        i = i + 1;
    }
    if i == nums.len() {
        -1
    } else {
        i as i32
    }
}
}