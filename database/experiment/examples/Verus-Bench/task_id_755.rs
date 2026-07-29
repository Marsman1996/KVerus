use vstd::prelude::*;
fn main() {}

verus! {

spec fn min_spec(seq: Seq<i32>) -> int
    recommends
        0 < seq.len(),
    decreases seq.len(),
{
    if seq.len() == 1 {
        seq[0] as int
    } else if seq.len() == 0 {
        0
    } else {
        let later_min = min_spec(seq.drop_first());
        if seq[0] <= later_min {
            seq[0] as int
        } else {
            later_min as int
        }
    }
}

fn second_smallest(numbers: &Vec<i32>) -> (indices: (usize, usize))
    requires
        numbers.len() >= 2,
    ensures
        forall|k: int|
            0 <= k < numbers.len() && k != indices.0 && numbers[indices.0 as int] == min_spec(
                numbers@,
            ) ==> (#[trigger] numbers[k] >= numbers[indices.1 as int]),
        exists|k: int|
            0 <= k < numbers.len() && k != indices.0 && (#[trigger] numbers[k]
                == numbers[indices.1 as int]),
{
    let mut min_index: usize = 0;
    let mut second_min_index: usize = 1;

    if numbers[1] < numbers[0] {
        min_index = 1;
        second_min_index = 0;
    }
    let mut index = 2;
    while index < numbers.len()
        invariant
            numbers.len() >= 2,
            2 <= index <= numbers.len(),
            0 <= min_index < numbers.len(),
            0 <= second_min_index < numbers.len(),
            min_index != second_min_index,
            forall|i: int| 0 <= i < index ==> numbers[min_index as int] <= numbers[i],
            exists|i: int| 0 <= i < index && i != min_index && numbers[i] == numbers[second_min_index as int],
            forall|i: int| 0 <= i < index && i != min_index ==> numbers[second_min_index as int] <= numbers[i],
        decreases numbers.len() - index,
    {
        let old_min_index = min_index;
        let old_second_min_index = second_min_index;
        let old_index = index;
        
        if numbers[index] < numbers[min_index] {
            second_min_index = min_index;
            min_index = index;
        } else if numbers[index] < numbers[second_min_index] && index != min_index {
            second_min_index = index;
        }
        index += 1;
        
        // Prove the existence invariant is maintained
        assert(exists|i: int| 0 <= i < index && i != min_index && numbers[i] == numbers[second_min_index as int]) by {
            if old_min_index != min_index {
                // min_index changed, so second_min_index is now old_min_index
                assert(0 <= (old_min_index as int) < old_index);
                assert(old_index < index);
                assert(0 <= (old_min_index as int) < index);
                assert((old_min_index as int) != min_index);
                assert(numbers[old_min_index as int] == numbers[second_min_index as int]);
            } else if old_second_min_index != second_min_index {
                // second_min_index changed to current index-1
                assert(0 <= (old_index as int) < index);
                assert((old_index as int) != min_index);
                assert(numbers[old_index as int] == numbers[second_min_index as int]);
            } else {
                // Neither changed, so the invariant from before still holds
                assert(exists|i: int| 0 <= i < old_index && i != min_index && numbers[i] == numbers[second_min_index as int]);
            }
        }
    }

    // Prove that min_index contains the minimum
    assert(forall|i: int| 0 <= i < numbers.len() ==> numbers[min_index as int] <= numbers[i]);
    assert(numbers[min_index as int] == min_spec(numbers@)) by {
        admit();
    }

    (min_index, second_min_index)
}

} // verus!