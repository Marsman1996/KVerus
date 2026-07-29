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
        invariant
            index <= arr.len(),
            forall|k: int| 0 <= k < index ==> (arr[k] % 2 == 0),
            arr@.take(index as int) == arr@.take(index as int).filter(|x: u32| x % 2 == 0),
        decreases arr.len() - index,
    {
        if (arr[index] % 2 != 0) {
            return Some(index);
        }
        assert(arr[index as int] % 2 == 0);
        reveal(Seq::filter);
        assert(arr@.take((index + 1) as int) == arr@.take(index as int).push(arr[index as int]));
        assert forall|s: Seq<u32>, x: u32| s == s.filter(|y: u32| y % 2 == 0) && x % 2 == 0 implies 
               s.push(x) == s.push(x).filter(|y: u32| y % 2 == 0) by {
            reveal(Seq::filter);
        }
        assert(arr@.take((index + 1) as int).filter(|x: u32| x % 2 == 0) == 
               arr@.take(index as int).filter(|x: u32| x % 2 == 0).push(arr[index as int]));
        index += 1;
    }
    None
}

fn main() {}

} // verus!