use vstd::prelude::*;

verus! {

spec fn is_upper_case(c: char) -> bool {
    c >= 'A' && c <= 'Z'
}

// This spec function computes uppercase character (i.e, ASCII code) sum.
spec fn count_uppercase_sum(seq: Seq<char>) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_uppercase_sum(seq.drop_last()) + if is_upper_case(seq.last()) {
            seq.last() as int
        } else {
            0 as int
        }
    }
}

// This function takes a string as input and returns the sum of the upper characters only'
fn digit_sum(text: &[char]) -> (sum: u128)
    ensures
        count_uppercase_sum(text@) == sum,
{
    let mut index = 0;
    let mut sum = 0u128;

    while index < text.len()
                                                                                                                                                                                                                                                                                                                                                                                                 
    {
        if (text[index] >= 'A' && text[index] <= 'Z') {
                                                                                                                                                        ;
            sum = sum + text[index] as u128;
        }
        index += 1;
                                                                                                  ;

    }
                                ;
                                                    ;
    sum
}

} // verus!

fn main() {}
