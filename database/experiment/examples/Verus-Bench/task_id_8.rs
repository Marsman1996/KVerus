use vstd::prelude::*;

fn main() {}

verus! {

fn square_nums(nums: &Vec<i32>) -> (squared: Vec<i32>)
    requires
        forall|k: int|
            0 <= k < nums.len() ==> (0 <= #[trigger] nums[k] * #[trigger] nums[k] < i32::MAX),
    ensures
        nums.len() == squared.len(),
        forall|k: int| 0 <= k < nums.len() ==> (#[trigger] squared[k] == nums[k] * nums[k]),
{
    let mut result: Vec<i32> = Vec::new();
    let mut index = 0;

    while index < nums.len()
        invariant
            0 <= index <= nums.len(),
            result.len() == index,
            forall|k: int| 0 <= k < index ==> (#[trigger] result[k] == nums[k] * nums[k]),
            forall|k: int| 0 <= k < nums.len() ==> (0 <= #[trigger] nums[k] * #[trigger] nums[k] < i32::MAX),
        decreases nums.len() - index,
    {
        result.push(nums[index] * nums[index]);
        index += 1;
    }
    result
}

} // verus!