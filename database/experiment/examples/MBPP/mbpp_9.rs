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

proof fn lemma_max_rcur_bound(seq: Seq<i32>, i: int)
    requires
        0 <= i < seq.len(),
        forall|j: int| 0 <= j < seq.len() ==> i32::MIN / 2 < #[trigger] seq[j] < i32::MAX / 2,
    ensures
        i32::MIN / 2 < max_rcur(seq.take(i + 1)) < i32::MAX / 2,
    decreases i,
{
    if i == 0 {
        assert(seq.take(1).len() == 1);
        assert(seq.take(1).first() == seq[0]);
    } else {
        lemma_max_rcur_bound(seq, i - 1);
        assert(seq.take(i + 1) =~= seq.take(i).push(seq[i]));
        assert(seq.take(i + 1).drop_last() =~= seq.take(i));
        assert(seq.take(i + 1).last() == seq[i]);
    }
}

proof fn lemma_min_rcur_bound(seq: Seq<i32>, i: int)
    requires
        0 <= i < seq.len(),
        forall|j: int| 0 <= j < seq.len() ==> i32::MIN / 2 < #[trigger] seq[j] < i32::MAX / 2,
    ensures
        i32::MIN / 2 < min_rcur(seq.take(i + 1)) < i32::MAX / 2,
    decreases i,
{
    if i == 0 {
        assert(seq.take(1).len() == 1);
        assert(seq.take(1).first() == seq[0]);
    } else {
        lemma_min_rcur_bound(seq, i - 1);
        assert(seq.take(i + 1) =~= seq.take(i).push(seq[i]));
        assert(seq.take(i + 1).drop_last() =~= seq.take(i));
        assert(seq.take(i + 1).last() == seq[i]);
    }
}

proof fn lemma_max_min_properties(seq: Seq<i32>, i: int)
    requires
        0 < i <= seq.len(),
        forall|j: int| 0 <= j < seq.len() ==> i32::MIN / 2 < #[trigger] seq[j] < i32::MAX / 2,
    ensures
        max_rcur(seq.take(i)) - min_rcur(seq.take(i)) < i32::MAX,
{
    lemma_max_rcur_bound(seq, i - 1);
    lemma_min_rcur_bound(seq, i - 1);
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
            min_val == min_rcur(arr@.take(index as int)),
            max_val == max_rcur(arr@.take(index as int)),
        decreases arr.len() - index,
    {
        proof {
            lemma_max_min_properties(arr@, index as int);
        }
        if (arr[index] <= min_val) {
            min_val = arr[index];
            proof {
                assert(arr@.take((index + 1) as int) =~= arr@.take(index as int).push(arr[index as int]));
                assert(arr@.take((index + 1) as int).drop_last() =~= arr@.take(index as int));
                assert(arr@.take((index + 1) as int).last() == arr[index as int]);
            }
        } else if (arr[index] > max_val) {
            max_val = arr[index];
            proof {
                assert(arr@.take((index + 1) as int) =~= arr@.take(index as int).push(arr[index as int]));
                assert(arr@.take((index + 1) as int).drop_last() =~= arr@.take(index as int));
                assert(arr@.take((index + 1) as int).last() == arr[index as int]);
            }
        } else {
            proof {
                assert(arr@.take((index + 1) as int) =~= arr@.take(index as int).push(arr[index as int]));
                assert(arr@.take((index + 1) as int).drop_last() =~= arr@.take(index as int));
                assert(arr@.take((index + 1) as int).last() == arr[index as int]);
            }
        }
        index += 1;
    }
    proof {
        assert(arr@ =~= arr@.take(arr.len() as int));
        lemma_max_min_properties(arr@, arr.len() as int);
    }
    max_val - min_val
}

fn main() {}

} // verus!