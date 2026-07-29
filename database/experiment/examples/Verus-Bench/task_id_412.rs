use vstd::prelude::*;

fn main() {}

verus! {

fn remove_odds(arr: &Vec<u32>) -> (even_list: Vec<u32>)
    ensures
        even_list@ == arr@.filter(|x: u32| x % 2 == 0),
{
    let mut even_list: Vec<u32> = Vec::new();
    let input_len = arr.len();

    let mut index = 0;
    while index < arr.len()
        invariant
            index <= arr@.len(),
            even_list@ == arr@.take(index as int).filter(|x: u32| x % 2 == 0),
        decreases arr@.len() - index,
    {
        if (arr[index] % 2 == 0) {
            even_list.push(arr[index]);
        }
        index += 1;
        
        assert(even_list@ == arr@.take(index as int).filter(|x: u32| x % 2 == 0)) by {
            let old_index = (index - 1) as int;
            assert(arr@.take(index as int) == arr@.take(old_index).push(arr[old_index]));
            vstd::seq::lemma_seq_filter_append(arr@.take(old_index), seq![arr[old_index]], |x: u32| x % 2 == 0);
        }
    }
    
    assert(arr@.take(arr@.len() as int) == arr@);
    even_list
}

} // verus!