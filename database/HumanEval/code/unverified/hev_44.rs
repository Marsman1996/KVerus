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

// This auxilary exe function computes the frequency of an element in a given sequence
fn count_frequency(elements: &Vec<i64>, key: i64) -> (frequency: usize)
    ensures
        count_frequency_spec(elements@, key) == frequency,
{
    let ghost elements_length = elements.len();
    let mut counter = 0;
    let mut index = 0;
    while index < elements.len()
                                                                                                                                                                                     
    {
        if (elements[index] == key) {
            counter += 1;
        }
        index += 1;
                                                                                                                                             ;
    }
                                                                      ;
    counter
}

//This function removes all elements that occur more than once
// Implementation following the ground-truth
fn remove_duplicates(numbers: &Vec<i64>) -> (unique_numbers: Vec<i64>)
    ensures
        unique_numbers@ == numbers@.filter(|x: i64| count_frequency_spec(numbers@, x) == 1),
{
    let ghost numbers_length = numbers.len();
    let mut unique_numbers: Vec<i64> = Vec::new();
    assert(numbers@.take(0int).filter(|x: i64| count_frequency_spec(numbers@, x) == 1) == Seq::<
        i64,
    >::empty());

    for index in 0..numbers.len()
        invariant
            0 <= index <= numbers.len(),
            unique_numbers@ == numbers@.take(index as int).filter(
                |x: i64| count_frequency_spec(numbers@, x) == 1,
            ),
    {
        if count_frequency(&numbers, numbers[index]) == 1 {
            unique_numbers.push(numbers[index]);
        }
        assert(numbers@.take((index + 1) as int).drop_last() == numbers@.take(index as int));
        reveal(Seq::filter);
    }
    assert(numbers@ == numbers@.take(numbers_length as int));
    unique_numbers
}

} // verus!

fn main() {}
