use vstd::prelude::*;

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
                                                                                                                                                   
    {
        if (arr[index] % 2 != 0) {
            return Some(index);
        }
                                                                                    ;
        reveal(Seq::filter);
        index += 1;
    }
                                               ;
    None
}

fn main() {}

} // verus!
