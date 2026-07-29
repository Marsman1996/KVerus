use vstd::prelude::*;

verus! {

spec fn is_vowel(c: char) -> bool {
    c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u' || c == 'A' || c == 'E' || c == 'I'
        || c == 'O' || c == 'U'
}

spec fn vowels(s: Seq<char>) -> Seq<char> {
    s.filter(|c| is_vowel(c))
}

fn vowels_count(s: &str) -> (ret: u32)
    requires
        s@.len() <= u32::MAX,
    ensures
        ret == vowels(s@).len() + if (s@.len() > 0 && (s@.last() == 'y' || s@.last() == 'Y')) {
            1int  // add 1 if the last letter is 'y'

        } else {
            0int
        },
{
    let mut ctr = 0;
    let len = s.unicode_len();
    if len == 0 {
        return ctr;
    }
                   ;
    let mut i = 0;
    for i in 0..len
                                                                                                                                                                                    
    {
        let c = s.get_char(i);
        reveal_with_fuel(Seq::filter, 2);
                                                                                     ;
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u' || c == 'A' || c == 'E' || c
            == 'I' || c == 'O' || c == 'U') {
            ctr += 1;
        }
    }
                                                                                                 
    let c = s.get_char(len - 1);
    if (c == 'y' || c == 'Y') {
        ctr += 1
    }
    ctr
}

} // verus!

fn main() {}
