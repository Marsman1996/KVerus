use vstd::prelude::*;

verus! {

fn find_even_numbers(arr: &Vec<u32>) -> (even_numbers: Vec<u32>)
    ensures
        even_numbers@ == arr@.filter(|x: u32| x % 2 == 0),
{
    let mut even_numbers: Vec<u32> = Vec::new();
    let input_len = arr.len();

                                                                              ;
    let mut index = 0;
    while index < arr.len()
                                                                                                                                        
    {
        if (arr[index] % 2 == 0) {
            even_numbers.push(arr[index]);
        }
                                                                                    ;
        reveal(Seq::filter);
        index += 1;
    }
                                               ;
    even_numbers
}

fn main() {}

} // verus!
