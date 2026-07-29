use vstd::prelude::*;

verus! {

// This spec function recursively computes the frequency of an element in a given sequence.
pub open spec fn count_frequency_spec(seq: Seq<i64>, key: i64) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_frequency_spec(seq.drop_last(), key) + if (seq.last() == key) {
            1 as int
        } else {
            0 as int
        }
    }
}

// Lemma to relate count_frequency_spec with take
proof fn lemma_count_frequency_take(seq: Seq<i64>, key: i64, i: int)
    requires
        0 <= i < seq.len(),
    ensures
        count_frequency_spec(seq.take(i + 1), key) == count_frequency_spec(seq.take(i), key) + if seq[i] == key { 1int } else { 0int },
    decreases i,
{
    reveal(Seq::take);
    assert(seq.take(i + 1) =~= seq.take(i).push(seq[i])) by {
        seq.lemma_take_succ_push(i);
    }
    let taken = seq.take(i);
    let elem = seq[i];
    assert(seq.take(i + 1).drop_last() =~= taken);
    assert(seq.take(i + 1).last() == elem);
}

// Lemma to show count_frequency_spec of full sequence equals count of take(len)
proof fn lemma_count_frequency_full(seq: Seq<i64>, key: i64)
    ensures
        count_frequency_spec(seq, key) == count_frequency_spec(seq.take(seq.len() as int), key),
{
    assert(seq.take(seq.len() as int) == seq) by {
        seq.lemma_take_len();
    }
}

// This auxilary exe function computes the frequency of an element in a given sequence
fn count_frequency(elements: &Vec<i64>, key: i64) -> (frequency: usize)
    ensures
        count_frequency_spec(elements@, key) == frequency,
{
    let ghost elements_length = elements.len();
    let mut counter = 0;
    let mut index = 0;
    while index < elements.len()
        invariant
            index <= elements.len(),
            counter == count_frequency_spec(elements@.take(index as int), key),
            counter <= index,
        decreases elements.len() - index,
    {
        proof {
            lemma_count_frequency_take(elements@, key, index as int);
        }
        if (elements[index] == key) {
            counter += 1;
        }
        index += 1;
    }
    proof {
        lemma_count_frequency_full(elements@, key);
    }
    counter
}

// Lemma to relate filter on take(i+1) with filter on take(i)
proof fn lemma_filter_take_push(numbers: Seq<i64>, i: int)
    requires
        0 <= i < numbers.len(),
    ensures
        numbers.take(i + 1).filter(|x: i64| count_frequency_spec(numbers, x) == 1) ==
        if count_frequency_spec(numbers, numbers[i]) == 1 {
            numbers.take(i).filter(|x: i64| count_frequency_spec(numbers, x) == 1).push(numbers[i])
        } else {
            numbers.take(i).filter(|x: i64| count_frequency_spec(numbers, x) == 1)
        },
{
    assert(numbers.take(i + 1) =~= numbers.take(i).push(numbers[i])) by {
        numbers.lemma_take_succ_push(i);
    }
    numbers.take(i).lemma_filter_push(numbers[i], |x: i64| count_frequency_spec(numbers, x) == 1);
}

// Lemma to show filter of full sequence equals filter of take(len)
proof fn lemma_filter_full(numbers: Seq<i64>)
    ensures
        numbers.filter(|x: i64| count_frequency_spec(numbers, x) == 1) ==
        numbers.take(numbers.len() as int).filter(|x: i64| count_frequency_spec(numbers, x) == 1),
{
    assert(numbers.take(numbers.len() as int) == numbers) by {
        numbers.lemma_take_len();
    }
}

//This function removes all elements that occur more than once
// Implementation following the ground-truth
fn remove_duplicates(numbers: &Vec<i64>) -> (unique_numbers: Vec<i64>)
    ensures
        unique_numbers@ == numbers@.filter(|x: i64| count_frequency_spec(numbers@, x) == 1),
{
    let ghost numbers_length = numbers.len();
    let mut unique_numbers: Vec<i64> = Vec::new();

    for index in 0..numbers.len()
        invariant
            unique_numbers@ == numbers@.take(index as int).filter(|x: i64| count_frequency_spec(numbers@, x) == 1),
    {
        proof {
            lemma_filter_take_push(numbers@, index as int);
        }
        if count_frequency(&numbers, numbers[index]) == 1 {
            unique_numbers.push(numbers[index]);
        }
        reveal(Seq::filter);
    }
    proof {
        lemma_filter_full(numbers@);
    }
    unique_numbers
}

fn main() {}

} // verus!