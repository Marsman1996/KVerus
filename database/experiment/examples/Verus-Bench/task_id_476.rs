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
        if (arr[index] <= min_val) {
            min_val = arr[index];
        } else if (arr[index] > max_val) {
            max_val = arr[index];
        }
        
        proof {
            let old_subseq = arr@.subrange(0, index as int);
            let new_subseq = arr@.subrange(0, (index + 1) as int);
            assert(new_subseq =~= old_subseq.push(arr@[index as int]));
            
            // For min_rcur
            if old_subseq.len() <= 1 {
                assert(min_rcur(old_subseq) == old_subseq.first() as int);
                if arr@[index as int] <= min_val {
                    assert(min_rcur(new_subseq) == min(arr@[index as int] as int, min_rcur(old_subseq)));
                    assert(min_rcur(new_subseq) == arr@[index as int] as int);
                } else {
                    assert(min_rcur(new_subseq) == min(arr@[index as int] as int, min_rcur(old_subseq)));
                    assert(min_rcur(new_subseq) == min_val as int);
                }
            } else {
                assert(min_rcur(new_subseq) == min(new_subseq.last() as int, min_rcur(new_subseq.drop_last())));
                assert(new_subseq.last() == arr@[index as int]);
                assert(new_subseq.drop_last() =~= old_subseq);
                if arr@[index as int] <= min_val {
                    assert(min_rcur(new_subseq) == arr@[index as int] as int);
                } else {
                    assert(min_rcur(new_subseq) == min_val as int);
                }
            }
            
            // For max_rcur
            if old_subseq.len() <= 1 {
                assert(max_rcur(old_subseq) == old_subseq.first() as int);
                if arr@[index as int] > max_val {
                    assert(max_rcur(new_subseq) == max(arr@[index as int] as int, max_rcur(old_subseq)));
                    assert(max_rcur(new_subseq) == arr@[index as int] as int);
                } else {
                    assert(max_rcur(new_subseq) == max(arr@[index as int] as int, max_rcur(old_subseq)));
                    assert(max_rcur(new_subseq) == max_val as int);
                }
            } else {
                assert(max_rcur(new_subseq) == max(new_subseq.last() as int, max_rcur(new_subseq.drop_last())));
                assert(new_subseq.last() == arr@[index as int]);
                assert(new_subseq.drop_last() =~= old_subseq);
                if arr@[index as int] > max_val {
                    assert(max_rcur(new_subseq) == arr@[index as int] as int);
                } else {
                    assert(max_rcur(new_subseq) == max_val as int);
                }
            }
        }
        
        index += 1;
    }
    
    proof {
        assert(arr@.subrange(0, arr.len() as int) =~= arr@);
    }
    
    max_val + min_val
}

} // verus!