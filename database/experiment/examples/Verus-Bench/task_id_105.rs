use vstd::prelude::*;

fn main() {}

verus! {

spec fn count_boolean(seq: Seq<bool>) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_boolean(seq.drop_last()) + if (seq.last()) {
            1 as int
        } else {
            0 as int
        }
    }
}

fn count_true(arr: &Vec<bool>) -> (count: u64)
    ensures
        0 <= count <= arr.len(),
        count_boolean(arr@) == count,
{
    let mut index = 0;
    let mut counter = 0;

    while index < arr.len()
        invariant
            0 <= index <= arr.len(),
            0 <= counter <= index,
            count_boolean(arr@.take(index as int)) == counter,
        decreases arr.len() - index,
    {
        if (arr[index]) {
            assert(counter < arr.len()) by {
                assert(counter <= index);
                assert(index < arr.len());
            }
            counter += 1;
        }
        index += 1;
        
        proof {
            if index > 1 {
                arr@.lemma_take_succ_push((index - 1) as int);
            }
            assert(arr@.take(index as int) == arr@.take((index - 1) as int).push(arr[index - 1]));
            
            // Prove the relationship between count_boolean of the extended sequence
            let prev_seq = arr@.take((index - 1) as int);
            let curr_seq = arr@.take(index as int);
            assert(curr_seq == prev_seq.push(arr[index - 1]));
            
            // Use the definition of count_boolean
            assert(curr_seq.len() > 0);
            assert(curr_seq.last() == arr[index - 1]);
            assert(curr_seq.drop_last() == prev_seq);
            assert(count_boolean(curr_seq) == count_boolean(curr_seq.drop_last()) + if curr_seq.last() { 1int } else { 0int });
            assert(count_boolean(curr_seq) == count_boolean(prev_seq) + if arr[index - 1] { 1int } else { 0int });
            
            if arr[index - 1] {
                assert(count_boolean(arr@.take(index as int)) == count_boolean(arr@.take((index - 1) as int)) + 1);
            } else {
                assert(count_boolean(arr@.take(index as int)) == count_boolean(arr@.take((index - 1) as int)));
            }
        }
    }
    
    proof {
        arr@.lemma_take_len();
    }
    
    counter
}

} // verus!