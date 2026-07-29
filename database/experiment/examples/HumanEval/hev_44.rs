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

proof fn lemma_count_frequency_skip(elements: Seq<i64>, key: i64, index: int)
    requires
        0 <= index < elements.len(),
    ensures
        count_frequency_spec(elements.skip(index), key) == 
            (if elements[index] == key { 1int } else { 0int }) + count_frequency_spec(elements.skip(index + 1), key),
    decreases elements.len() - index,
{
    let skipped = elements.skip(index);
    assert(skipped.len() > 0);
    assert(skipped[0] == elements[index]);
    assert(skipped.drop_last() =~= skipped.take((skipped.len() - 1) as int));
    assert(skipped.skip(1) =~= elements.skip(index + 1));
    
    // The key insight: we need to relate the recursive definition to the skip operation
    if skipped.len() == 1 {
        assert(skipped.skip(1) =~= Seq::<i64>::empty());
        assert(count_frequency_spec(skipped.skip(1), key) == 0);
        assert(skipped.last() == skipped[0]);
        assert(skipped[0] == elements[index]);
    } else {
        // For longer sequences, we need to show the recursive structure
        lemma_count_frequency_skip(elements, key, index + 1);
        assert(skipped.drop_last().skip(1) =~= skipped.skip(1).drop_last());
        
        // Prove the relationship step by step
        assert(count_frequency_spec(skipped.skip(1), key) == 
            (if elements[index + 1] == key { 1int } else { 0int }) + count_frequency_spec(elements.skip(index + 2), key));
        
        // Show that skipped.drop_last() == skipped.skip(1).drop_last() prepended with skipped[0]
        assert(skipped.drop_last() =~= skipped.take(skipped.len() - 1));
        assert(skipped.skip(1).drop_last() =~= skipped.skip(1).take(skipped.len() - 2));
        
        // Recursively apply to drop_last
        if skipped.drop_last().len() > 0 {
            lemma_count_frequency_skip(elements, key, index + 1);
        }
    }
    
    assert(count_frequency_spec(skipped, key) == count_frequency_spec(skipped.drop_last(), key) + if skipped.last() == key { 1int } else { 0int });
    assert(skipped.last() == skipped[skipped.len() - 1]);
    assert(skipped[skipped.len() - 1] == elements[index + skipped.len() - 1]);
    assert(skipped[0] == elements[index]);
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
            0 <= index <= elements.len(),
            counter == count_frequency_spec(elements@.take(index as int), key),
            counter <= index,
        decreases elements.len() - index,
    {
        if (elements[index] == key) {
            counter += 1;
        }
        index += 1;
        proof {
            let old_index = (index - 1) as int;
            lemma_count_frequency_skip(elements@, key, old_index);
            assert(elements@.take(index as int) =~= elements@.take(old_index).push(elements@[old_index]));

            let current_take = elements@.take(old_index);
            let next_take = elements@.take(index as int);
            assert(next_take == current_take.push(elements@[old_index]));

            if next_take.len() > 0 {
                assert(next_take.drop_last() =~= current_take);
                assert(next_take.last() == elements@[old_index]);
                assert(count_frequency_spec(next_take, key) ==
                    count_frequency_spec(next_take.drop_last(), key) +
                    (if next_take.last() == key { 1int } else { 0int }));
            }

            assert(count_frequency_spec(next_take, key) ==
                count_frequency_spec(current_take, key) +
                (if elements@[old_index] == key { 1int } else { 0int }));
        }
    }
    assert(elements@ == elements@.take(elements_length as int));
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
