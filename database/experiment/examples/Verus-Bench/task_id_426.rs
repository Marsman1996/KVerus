use vstd::prelude::*;

fn main() {}

verus! {

fn filter_odd_numbers(arr: &Vec<u32>) -> (odd_list: Vec<u32>)
    ensures
        odd_list@ == arr@.filter(|x: u32| x % 2 != 0),
{
    let mut odd_list: Vec<u32> = Vec::new();
    let input_len = arr.len();

    let mut index = 0;
    while index < arr.len()
        invariant
            index <= arr@.len(),
            odd_list@ == arr@.subrange(0, index as int).filter(|x: u32| x % 2 != 0),
        decreases arr@.len() - index,
    {
        if (arr[index] % 2 != 0) {
            odd_list.push(arr[index]);
        }
        index += 1;

        proof {
            let pred = |x: u32| x % 2 != 0;
            let prev_subrange = arr@.subrange(0, (index - 1) as int);
            let curr_subrange = arr@.subrange(0, index as int);
            
            // Show that curr_subrange is prev_subrange.push(arr[index - 1])
            assert(curr_subrange == prev_subrange.push(arr[(index - 1) as int]));
            
            // Apply the filter push lemma
            prev_subrange.lemma_filter_push(arr[(index - 1) as int], pred);
        }
    }
    
    proof {
        // After the loop, index == arr@.len()
        assert(index == arr@.len());
        // So arr@.subrange(0, index as int) == arr@
        assert(arr@.subrange(0, index as int) == arr@);
    }
    
    odd_list
}

} // verus!