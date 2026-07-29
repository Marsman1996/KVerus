use vstd::prelude::*;

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
            index <= arr.len(),
            even_list@ == arr@.subrange(0, index as int).filter(|x: u32| x % 2 == 0),
        decreases arr.len() - index,
    {
        assert(arr@.subrange(0, index as int).push(arr[index as int]) =~= arr@.subrange(0, (index + 1) as int)) by {
            assert(arr@.subrange(0, index as int).len() == index as int);
            assert(arr@.subrange(0, (index + 1) as int).len() == (index + 1) as int);
            assert forall |i: int| 0 <= i < index implies arr@.subrange(0, index as int)[i] == arr@.subrange(0, (index + 1) as int)[i] by {
                assert(arr@.subrange(0, index as int)[i] == arr@[i]);
                assert(arr@.subrange(0, (index + 1) as int)[i] == arr@[i]);
            }
            assert(arr@.subrange(0, (index + 1) as int)[index as int] == arr@[index as int]);
        }
        
        let old_even_list = Ghost(even_list@);
        if (arr[index] % 2 == 0) {
            even_list.push(arr[index]);
        }
        
        proof {
            assert(even_list@ == arr@.subrange(0, (index + 1) as int).filter(|x: u32| x % 2 == 0)) by {
                reveal(Seq::filter);
                assert(arr@.subrange(0, (index + 1) as int) =~= arr@.subrange(0, index as int).push(arr[index as int]));
                if arr[index as int] % 2 == 0 {
                    assert(even_list@ == old_even_list@.push(arr[index as int]));
                } else {
                    assert(even_list@ == old_even_list@);
                }
            }
        }
        
        index += 1;
    }
    
    assert(arr@.subrange(0, index as int) =~= arr@);
    
    even_list
}

fn main() {}

} // verus!