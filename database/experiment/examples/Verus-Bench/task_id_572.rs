use vstd::prelude::*;

fn main() {}

verus! {

pub open spec fn count_frequency_rcr(seq: Seq<i32>, key: i32) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_frequency_rcr(seq.drop_last(), key) + if (seq.last() == key) {
            1 as int
        } else {
            0 as int
        }
    }
}

proof fn lemma_count_frequency_rcr_take_succ(seq: Seq<i32>, key: i32, i: int)
    requires
        0 <= i < seq.len(),
    ensures
        count_frequency_rcr(seq.take(i + 1), key) == count_frequency_rcr(seq.take(i), key) + if seq[i] == key { 1int } else { 0int },
    decreases seq.len() - i,
{
    seq.lemma_take_succ_push(i);
    assert(seq.take(i + 1) =~= seq.take(i).push(seq[i]));
    
    if seq.take(i + 1).len() == 0 {
        assert(false);
    } else {
        assert(seq.take(i + 1).drop_last() =~= seq.take(i));
        assert(seq.take(i + 1).last() == seq[i]);
    }
}

proof fn lemma_count_frequency_rcr_full(seq: Seq<i32>, key: i32)
    ensures
        count_frequency_rcr(seq, key) == count_frequency_rcr(seq.take(seq.len() as int), key),
{
    assert(seq =~= seq.take(seq.len() as int));
}

fn count_frequency(arr: &Vec<i32>, key: i32) -> (frequency: usize)
    ensures
        count_frequency_rcr(arr@, key) == frequency,
{
    let mut index = 0;
    let mut counter = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            counter == count_frequency_rcr(arr@.take(index as int), key),
            counter <= index,
        decreases arr.len() - index,
    {
        if (arr[index] == key) {
            counter += 1;
        }
        proof {
            lemma_count_frequency_rcr_take_succ(arr@, key, index as int);
        }
        index += 1;
    }
    proof {
        lemma_count_frequency_rcr_full(arr@, key);
    }
    counter
}

proof fn lemma_filter_take_succ(seq: Seq<i32>, i: int, pred: spec_fn(i32) -> bool)
    requires
        0 <= i < seq.len(),
    ensures
        seq.take(i + 1).filter(pred) == seq.take(i).filter(pred) + if pred(seq[i]) { seq![seq[i]] } else { Seq::empty() },
{
    seq.lemma_take_succ_push(i);
    assert(seq.take(i + 1) =~= seq.take(i).push(seq[i]));
    seq.take(i).lemma_filter_push(seq[i], pred);
}

proof fn lemma_filter_full(seq: Seq<i32>, pred: spec_fn(i32) -> bool)
    ensures
        seq.filter(pred) == seq.take(seq.len() as int).filter(pred),
{
    assert(seq =~= seq.take(seq.len() as int));
}

fn remove_duplicates(arr: &Vec<i32>) -> (unique_arr: Vec<i32>)
    ensures
        unique_arr@ == arr@.filter(|x: i32| count_frequency_rcr(arr@, x) == 1),
{
    let mut unique_arr: Vec<i32> = Vec::new();
    let input_len = arr.len();
    let mut index = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            unique_arr@ == arr@.take(index as int).filter(|x: i32| count_frequency_rcr(arr@, x) == 1),
        decreases arr.len() - index,
    {
        if count_frequency(&arr, arr[index]) == 1 {
            unique_arr.push(arr[index]);
        }
        proof {
            lemma_filter_take_succ(arr@, index as int, |x: i32| count_frequency_rcr(arr@, x) == 1);
        }
        index += 1;
    }
    proof {
        lemma_filter_full(arr@, |x: i32| count_frequency_rcr(arr@, x) == 1);
    }
    unique_arr
}

} // verus!