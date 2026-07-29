#![verifier::loop_isolation(false)]
use vstd::math::*;
use vstd::prelude::*;

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

proof fn lemma_max_rcur_properties(seq: Seq<i32>, i: int)
    requires
        seq.len() > 0,
        0 <= i < seq.len(),
    ensures
        seq[i] <= max_rcur(seq),
    decreases seq.len(),
{
    if seq.len() <= 1 {
    } else {
        if i == seq.len() - 1 {
        } else {
            lemma_max_rcur_properties(seq.drop_last(), i);
        }
    }
}

proof fn lemma_min_rcur_properties(seq: Seq<i32>, i: int)
    requires
        seq.len() > 0,
        0 <= i < seq.len(),
    ensures
        min_rcur(seq) <= seq[i],
    decreases seq.len(),
{
    if seq.len() <= 1 {
    } else {
        if i == seq.len() - 1 {
        } else {
            lemma_min_rcur_properties(seq.drop_last(), i);
        }
    }
}

fn sum_min_max(arr: &Vec<i32>) -> (sum: i32)
    requires
        arr.len() > 0,
        forall|i: int| 0 <= i < arr.len() ==> i32::MIN / 2 < #[trigger] arr[i] < i32::MAX / 2,
    ensures
        sum == max_rcur(arr@) + min_rcur(arr@),
{
    let mut min_val = arr[0];
    let mut max_val = arr[0];
    let mut index = 1;

    proof {
        lemma_max_rcur_properties(arr@, 0);
        lemma_min_rcur_properties(arr@, 0);
    }

    while index < arr.len()
        invariant
            arr.len() > 0,
            forall|i: int| 0 <= i < arr.len() ==> i32::MIN / 2 < #[trigger] arr[i] < i32::MAX / 2,
            1 <= index <= arr.len(),
            min_val <= min_rcur(arr@),
            max_val >= max_rcur(arr@),
            forall|i: int| 0 <= i < index ==> min_val <= arr[i],
            forall|i: int| 0 <= i < index ==> max_val >= arr[i],
        decreases arr.len() - index,
    {
        proof {
            lemma_max_rcur_properties(arr@, index as int);
            lemma_min_rcur_properties(arr@, index as int);
        }
        if (arr[index] <= min_val) {
            min_val = arr[index];
        } else if (arr[index] > max_val) {
            max_val = arr[index];
        }
        index += 1;
    }
    
    proof {
        assert(forall|i: int| 0 <= i < arr.len() ==> min_val <= arr[i]);
        assert(forall|i: int| 0 <= i < arr.len() ==> max_val >= arr[i]);
        assert forall|i: int| 0 <= i < arr.len() implies min_rcur(arr@) <= arr[i] by {
            lemma_min_rcur_properties(arr@, i);
        }
        assert forall|i: int| 0 <= i < arr.len() implies arr[i] <= max_rcur(arr@) by {
            lemma_max_rcur_properties(arr@, i);
        }
        assert(min_val == min_rcur(arr@));
        assert(max_val == max_rcur(arr@));
    }
    
    max_val + min_val
}

fn main() {}

} // verus!