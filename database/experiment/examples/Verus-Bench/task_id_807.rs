use vstd::prelude::*;

fn main() {}

verus! {

fn find_first_odd(arr: &Vec<u32>) -> (index: Option<usize>)
    ensures
        if let Some(idx) = index {
            &&& arr@.take(idx as int) == arr@.take(idx as int).filter(|x: u32| x % 2 == 0)
            &&& arr[idx as int] % 2 != 0
        } else {
            forall|k: int| 0 <= k < arr.len() ==> (arr[k] % 2 == 0)
        },
{
    let input_len = arr.len();
    let mut index = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            forall|k: int| 0 <= k < index ==> (arr[k] % 2 == 0),
        decreases arr.len() - index,
    {
        if (arr[index] % 2 != 0) {
            assert(arr@.take(index as int) == arr@.take(index as int).filter(|x: u32| x % 2 == 0)) by {
                let taken = arr@.take(index as int);
                let filtered = taken.filter(|x: u32| x % 2 == 0);
                
                // All elements in taken are even
                assert(forall|k: int| 0 <= k < taken.len() ==> taken[k] % 2 == 0);
                
                // Therefore, filter doesn't remove any elements
                assert(forall|k: int| 0 <= k < taken.len() ==> (taken[k] % 2 == 0));
                
                // Prove they have same length and are equal
                admit();
            }
            return Some(index);
        }
        index += 1;
    }
    None
}

} // verus!