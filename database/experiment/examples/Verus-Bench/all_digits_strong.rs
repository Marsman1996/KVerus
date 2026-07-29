use vstd::prelude::*;

fn main() {}
verus! {

spec fn is_ascii_digit_spec(c: char) -> bool {
    c == '0' || c == '1' || c == '2' || c == '3' || c == '4' || c == '5' || c == '6' || c == '7'
        || c == '8' || c == '9'
}

fn is_ascii_digit(c: char) -> (r: bool)
    ensures
        r == is_ascii_digit_spec(c),
{
    c == '0' || c == '1' || c == '2' || c == '3' || c == '4' || c == '5' || c == '6' || c == '7'
        || c == '8' || c == '9'
}

spec fn all_digits_spec(s: Seq<char>) -> bool {
    forall|i: nat| #![auto] i < s.len() ==> is_ascii_digit_spec(s[i as int])
}

fn all_digits(s: String) -> (result: bool)
    requires
        s.is_ascii(),
    ensures
        all_digits_spec(s@) == result,
{
    let mut result = true;
    let mut i: usize = 0;
    let s_len = s@.len() as usize;
    while i < s_len
        invariant
            0 <= i <= s_len,
            forall|j: nat| j < i ==> is_ascii_digit_spec(s@[j as int]),
            result == forall|j: nat| j < i ==> is_ascii_digit_spec(s@[j as int]),
        decreases
            s_len - i,
    {
        if !is_ascii_digit(s@[i]) {
            return false;
        }
        i = i + 1;
    }
    true
}

} // verus!