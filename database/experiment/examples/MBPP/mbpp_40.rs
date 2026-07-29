use vstd::prelude::*;

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

proof fn sum_negative_to_take_lemma(seq: Seq<i64>, i: int)
    requires
        0 <= i < seq.len(),
    ensures
        sum_negative_to(seq.take(i + 1)) == sum_negative_to(seq.take(i)) + if seq[i] < 0 { seq[i] as int } else { 0 },
{
    assert(seq.take(i + 1) =~= seq.take(i).push(seq[i]));
    let s = seq.take(i);
    let s_plus = seq.take(i + 1);
    assert(s_plus.drop_last() =~= s);
    assert(s_plus.last() == seq[i]);
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
            sum_neg >= i128::MIN,
            sum_neg <= i128::MAX,
            forall|j: int| 0 <= j < index ==> arr@[j] >= i64::MIN && arr@[j] <= i64::MAX,
            sum_neg >= (index as i128) * (i64::MIN as i128),
            sum_neg <= (index as i128) * (i64::MAX as i128),
        decreases arr.len() - index,
    {
        if (arr[index] < 0) {
            proof {
                sum_negative_to_take_lemma(arr@, index as int);
            }
            assert(sum_neg + (arr@[index as int] as i128) >= i128::MIN);
            assert(sum_neg + (arr@[index as int] as i128) <= i128::MAX);
            sum_neg = sum_neg + (arr[index] as i128);
        } else {
            proof {
                sum_negative_to_take_lemma(arr@, index as int);
            }
        }
        index += 1;
    }
    assert(arr@.take(index as int) =~= arr@);
    sum_neg
}

fn main() {}

} // verus!