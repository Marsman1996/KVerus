#![verifier::loop_isolation(false)]
use vstd::math::*;
use vstd::prelude::*;

fn main() {}

verus! {

spec fn max_rcur(seq: Seq<i32>) -> int
    decreases seq.len(),
{
    if seq.len() <= 1 {
        seq.first() as int
    } else {
        max(seq.last() as int, max_rcur(seq.drop_last()))
    }
}

spec fn min_rcur(seq: Seq<i32>) -> int
    decreases seq.len(),
{
    if seq.len() <= 1 {
        seq.first() as int
    } else {
        min(seq.last() as int, min_rcur(seq.drop_last()))
    }
}

proof fn lemma_max_rcur_equals_max(seq: Seq<i32>)
    requires seq.len() > 0,
    ensures max_rcur(seq) == max_rcur(seq),
    decreases seq.len(),
{
    if seq.len() == 1 {
        // base case
    } else {
        lemma_max_rcur_equals_max(seq.drop_last());
    }
}

proof fn lemma_min_rcur_equals_min(seq: Seq<i32>)
    requires seq.len() > 0,
    ensures min_rcur(seq) == min_rcur(seq),
    decreases seq.len(),
{
    if seq.len() == 1 {
        // base case
    } else {
        lemma_min_rcur_equals_min(seq.drop_last());
    }
}

proof fn lemma_max_min_subrange(seq: Seq<i32>, i: int)
    requires 
        seq.len() > 0,
        1 <= i < seq.len(),
    ensures 
        max_rcur(seq.subrange(0, i + 1)) == max(seq[i] as int, max_rcur(seq.subrange(0, i))),
        min_rcur(seq.subrange(0, i + 1)) == min(seq[i] as int, min_rcur(seq.subrange(0, i))),
{
    let sub_i = seq.subrange(0, i);
    let sub_i_plus_1 = seq.subrange(0, i + 1);
    
    assert(sub_i_plus_1.drop_last() == sub_i);
    assert(sub_i_plus_1.last() == seq[i]);
}

fn difference_max_min(arr: &Vec<i32>) -> (diff: i32)
    requires
        arr.len() > 0,
        forall|i: int| 0 <= i < arr.len() ==> i32::MIN / 2 < #[trigger] arr[i] < i32::MAX / 2,
    ensures
        diff == max_rcur(arr@) - min_rcur(arr@),
{
    let mut min_val = arr[0];
    let mut max_val = arr[0];
    let mut index = 1;

    while index < arr.len()
        invariant
            arr.len() > 0,
            forall|i: int| 0 <= i < arr.len() ==> i32::MIN / 2 < #[trigger] arr[i] < i32::MAX / 2,
            1 <= index <= arr.len(),
            min_val == min_rcur(arr@.subrange(0, index as int)),
            max_val == max_rcur(arr@.subrange(0, index as int)),
            i32::MIN / 2 < min_val < i32::MAX / 2,
            i32::MIN / 2 < max_val < i32::MAX / 2,
        decreases arr.len() - index,
    {
        proof {
            lemma_max_min_subrange(arr@, index as int);
        }
        
        if (arr[index] <= min_val) {
            min_val = arr[index];
        } else if (arr[index] > max_val) {
            max_val = arr[index];
        }
        index += 1;
    }
    
    proof {
        lemma_max_rcur_equals_max(arr@);
        lemma_min_rcur_equals_min(arr@);
        assert(arr@.subrange(0, arr.len() as int) == arr@);
    }
    
    max_val - min_val
}

} // verus!