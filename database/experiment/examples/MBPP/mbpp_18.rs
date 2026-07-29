use vstd::prelude::*;

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
            index <= arr.len(),
            odd_list@ == arr@.subrange(0, index as int).filter(|x: u32| x % 2 != 0),
        decreases arr.len() - index,
    {
        proof {
            assert(arr@.subrange(0, index as int + 1) =~= arr@.subrange(0, index as int).push(arr@[index as int]));
            reveal(Seq::filter);
            if arr@[index as int] % 2 != 0 {
                assert forall |i: int| 0 <= i < arr@.subrange(0, index as int).len() implies 
                    arr@.subrange(0, index as int)[i] % 2 != 0 <==> 
                    arr@.subrange(0, index as int).push(arr@[index as int])[i] % 2 != 0 by {};
                assert(arr@.subrange(0, index as int).push(arr@[index as int])[arr@.subrange(0, index as int).len() as int] % 2 != 0);
                vstd::seq_lib::lemma_seq_filter_append(arr@.subrange(0, index as int), seq![arr@[index as int]], |x: u32| x % 2 != 0);
            } else {
                assert forall |i: int| 0 <= i < arr@.subrange(0, index as int).len() implies 
                    arr@.subrange(0, index as int)[i] % 2 != 0 <==> 
                    arr@.subrange(0, index as int).push(arr@[index as int])[i] % 2 != 0 by {};
                assert(arr@.subrange(0, index as int).push(arr@[index as int])[arr@.subrange(0, index as int).len() as int] % 2 == 0);
                vstd::seq_lib::lemma_seq_filter_append(arr@.subrange(0, index as int), seq![arr@[index as int]], |x: u32| x % 2 != 0);
            }
        }
        if (arr[index] % 2 != 0) {
            odd_list.push(arr[index]);
        }
        index += 1;
    }
    proof {
        assert(arr@.subrange(0, index as int) =~= arr@);
    }
    odd_list
}

fn main() {}

} // verus!