use vstd::prelude::*;

fn main() {}

verus! {

fn find_odd_numbers(arr: &Vec<u32>) -> (odd_numbers: Vec<u32>)
    ensures
        odd_numbers@ == arr@.filter(|x: u32| x % 2 != 0),
{
    let mut odd_numbers: Vec<u32> = Vec::new();
    let input_len = arr.len();

    let mut index = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            odd_numbers@ == arr@.subrange(0, index as int).filter(|x: u32| x % 2 != 0),
        decreases arr.len() - index,
    {
        if (arr[index] % 2 != 0) {
            odd_numbers.push(arr[index]);
        }
        index += 1;

        // Proof that the invariant is maintained
        proof {
            let pred = |x: u32| x % 2 != 0;
            let old_subrange = arr@.subrange(0, (index - 1) as int);
            let new_subrange = arr@.subrange(0, index as int);
            
            // Show that new_subrange equals old_subrange.push(arr[index - 1])
            assert(new_subrange == old_subrange.push(arr[(index - 1) as int]));
            
            // Use the filter_push lemma
            old_subrange.lemma_filter_push(arr[(index - 1) as int], pred);
        }
    }
    
    // Proof that postcondition holds
    proof {
        assert(index == arr.len());
        assert(arr@.subrange(0, index as int) == arr@);
    }
    
    odd_numbers
}

} // verus!