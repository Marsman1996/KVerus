use vstd::prelude::*;

verus! {

fn get_positive(input: Vec<i32>) -> (positive_list: Vec<i32>)
    ensures
        positive_list@ == input@.filter(|x: i32| x > 0),
{
    let mut positive_list = Vec::<i32>::new();
    let input_len = input.len();
                                                                           ;
    for pos in 0..input_len
                                                                                                                                     
    {
        let n = input[pos];
        if n > 0 {
            positive_list.push(n);
        }
                                                                                    ;
        reveal(Seq::filter);
    }
                                                   ;
    positive_list
}

} // verus!

fn main() {}
