use vstd::prelude::*;

fn main() {}

verus! {

fn find_negative_numbers(arr: &Vec<i32>) -> (negative_list: Vec<i32>)
    ensures
        negative_list@ == arr@.filter(|x: i32| x < 0),
{
    let mut negative_list: Vec<i32> = Vec::new();
    let mut index = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            negative_list@ == arr@.subrange(0, index as int).filter(|x: i32| x < 0),
        decreases arr.len() - index,
    {
        if (arr[index] < 0) {
            negative_list.push(arr[index]);
        }
        index += 1;
        
        proof {
            let old_subrange = arr@.subrange(0, (index - 1) as int);
            let new_subrange = arr@.subrange(0, index as int);
            assert(new_subrange == old_subrange.push(arr[index - 1]));
            
            if arr[index - 1] < 0 {
                old_subrange.lemma_filter_push(arr[index - 1], |x: i32| x < 0);
            } else {
                old_subrange.lemma_filter_push(arr[index - 1], |x: i32| x < 0);
            }
        }
    }
    
    proof {
        assert(index == arr.len());
        assert(arr@.subrange(0, index as int) == arr@.subrange(0, arr.len() as int));
        assert(arr@.subrange(0, arr.len() as int) == arr@);
    }
    
    negative_list
}

} // verus!