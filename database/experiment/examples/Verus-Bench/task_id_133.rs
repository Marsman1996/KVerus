use vstd::prelude::*;

fn main() {}

verus! {

spec fn sum_negative_to(seq: Seq<i64>) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        sum_negative_to(seq.drop_last()) + if (seq.last() < 0) {
            seq.last() as int
        } else {
            0 as int
        }
    }
}

proof fn sum_negative_to_take_lemma(arr: Seq<i64>, i: int)
    requires
        0 <= i < arr.len(),
    ensures
        sum_negative_to(arr.take(i + 1)) == sum_negative_to(arr.take(i)) + if arr[i] < 0 { arr[i] as int } else { 0 },
    decreases i,
{
    if i == 0 {
        assert(arr.take(1).drop_last() =~= arr.take(0));
        assert(arr.take(1).last() == arr[0]);
    } else {
        sum_negative_to_take_lemma(arr, i - 1);
        assert(arr.take(i + 1).drop_last() =~= arr.take(i));
        assert(arr.take(i + 1).last() == arr[i]);
    }
}

fn sum_negatives(arr: &Vec<i64>) -> (sum_neg: i128)
    ensures
        sum_negative_to(arr@) == sum_neg,
{
    let mut index = 0;
    let mut sum_neg = 0i128;

    while index < arr.len()
        invariant
            index <= arr.len(),
            sum_neg == sum_negative_to(arr@.take(index as int)),
            -0x8000_0000_0000_0000i128 * (index as i128) <= sum_neg <= 0,
        decreases arr.len() - index,
    {
        let old_index = index;
        if (arr[index] < 0) {
            sum_neg = sum_neg + (arr[index] as i128);
        }
        index += 1;
        assert(arr@.take(index as int) =~= arr@.take((index - 1) as int).push(arr@[(index - 1) as int])) by {
            arr@.lemma_take_succ_push((index - 1) as int);
        }
        proof {
            sum_negative_to_take_lemma(arr@, old_index as int);
        }
        assert(sum_negative_to(arr@.take(index as int)) == 
               sum_negative_to(arr@.take(old_index as int)) + 
               if arr@[old_index as int] < 0 { arr@[old_index as int] as int } else { 0 });
    }
    assert(arr@.take(index as int) =~= arr@);
    sum_neg
}

} // verus!