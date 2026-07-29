use vstd::prelude::*;

fn main() {}

verus! {

fn find_even_numbers(arr: &Vec<u32>) -> (even_numbers: Vec<u32>)
    ensures
        even_numbers@ == arr@.filter(|x: u32| x % 2 == 0),
{
    let mut even_numbers: Vec<u32> = Vec::new();
    let mut index = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            even_numbers@ == arr@.take(index as int).filter(|x: u32| x % 2 == 0),
        decreases arr.len() - index,
    {
        proof {
            assert(arr@.take((index + 1) as int) =~= arr@.take(index as int).push(arr@[index as int])) by {
                arr@.lemma_take_succ_push(index as int);
            }
            assert(arr@.take((index + 1) as int).filter(|x: u32| x % 2 == 0) == 
                   if arr@[index as int] % 2 == 0 {
                       arr@.take(index as int).filter(|x: u32| x % 2 == 0).push(arr@[index as int])
                   } else {
                       arr@.take(index as int).filter(|x: u32| x % 2 == 0)
                   }) by {
                arr@.take(index as int).lemma_filter_push(arr@[index as int], |x: u32| x % 2 == 0);
            }
        }
        if (arr[index] % 2 == 0) {
            even_numbers.push(arr[index]);
        }
        index += 1;
    }
    proof {
        assert(arr@.take(index as int) =~= arr@);
    }
    even_numbers
}

} // verus!