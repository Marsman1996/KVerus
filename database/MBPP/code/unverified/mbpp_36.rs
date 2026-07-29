use vstd::prelude::*;

verus! {

fn find_negative_numbers(arr: &Vec<i32>) -> (negative_list: Vec<i32>)
    ensures
        negative_list@ == arr@.filter(|x: i32| x < 0),
{
    let mut negative_list: Vec<i32> = Vec::new();
    let input_len = arr.len();

                                                                         ;
    let mut index = 0;
    while index < arr.len()
                                                                                                                                    
    {
        if (arr[index] < 0) {
            negative_list.push(arr[index]);
        }
                                                                                    ;
        reveal(Seq::filter);
        index += 1;
    }
                                               ;
    negative_list
}

fn main() {}

} // verus!
