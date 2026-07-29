use vstd::prelude::*;

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

proof fn lemma_count_frequency_take_succ(seq: Seq<i32>, key: i32, i: int)
    requires
        0 <= i < seq.len(),
    ensures
        count_frequency_rcr(seq.take(i + 1), key) == count_frequency_rcr(seq.take(i), key) + if seq[i] == key { 1int } else { 0int },
{
    assert(seq.take(i + 1) =~= seq.take(i).push(seq[i]));
    let taken = seq.take(i + 1);
    assert(taken.drop_last() =~= seq.take(i));
    assert(taken.last() == seq[i]);
}

proof fn lemma_count_frequency_full(seq: Seq<i32>, key: i32)
    ensures
        count_frequency_rcr(seq.take(seq.len() as int), key) == count_frequency_rcr(seq, key),
{
    assert(seq.take(seq.len() as int) == seq);
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
        proof {
            lemma_count_frequency_take_succ(arr@, key, index as int);
        }
        if (arr[index] == key) {
            counter += 1;
        }
        index += 1;
    }
    proof {
        lemma_count_frequency_full(arr@, key);
    }
    counter
}

proof fn lemma_filter_take_succ(seq: Seq<i32>, pred: spec_fn(i32) -> bool, i: int)
    requires
        0 <= i < seq.len(),
    ensures
        seq.take(i + 1).filter(pred) == if pred(seq[i]) {
            seq.take(i).filter(pred).push(seq[i])
        } else {
            seq.take(i).filter(pred)
        },
{
    reveal(Seq::filter);
    assert(seq.take(i + 1) =~= seq.take(i).push(seq[i]));
}

proof fn lemma_filter_full(seq: Seq<i32>, pred: spec_fn(i32) -> bool)
    ensures
        seq.take(seq.len() as int).filter(pred) == seq.filter(pred),
{
    assert(seq.take(seq.len() as int) == seq);
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
        proof {
            lemma_filter_take_succ(arr@, |x: i32| count_frequency_rcr(arr@, x) == 1, index as int);
        }
        if count_frequency(&arr, arr[index]) == 1 {
            unique_arr.push(arr[index]);
        }
        reveal(Seq::filter);
        index += 1;
    }
    proof {
        lemma_filter_full(arr@, |x: i32| count_frequency_rcr(arr@, x) == 1);
    }
    unique_arr
}

fn main() {}

} // verus!