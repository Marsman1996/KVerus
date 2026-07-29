use vstd::prelude::*;

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
        
        proof {
            assert(arr@.subrange(0, index as int + 1) =~= arr@.subrange(0, index as int) + seq![arr[index as int]]);
            vstd::seq_lib::lemma_seq_filter_distributes_over_add(arr@.subrange(0, index as int), seq![arr[index as int]], |x: u32| x % 2 != 0);
        }
        
        index += 1;
    }
    
    assert(arr@.subrange(0, index as int) =~= arr@);
    
    odd_numbers
}

fn main() {}

} // verus!