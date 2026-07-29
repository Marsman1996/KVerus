use vstd::prelude::*;

verus! {

// This spec function checks whether a character is a vowel
pub open spec fn is_vowel_spec(c: char) -> bool {
    c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u' || c == 'A' || c == 'E' || c == 'I'
        || c == 'O' || c == 'U'
}

// This auxilary exec function checks whether a character is a vowel
fn is_vowel(c: char) -> (is_vowel: bool)
    ensures
        is_vowel == is_vowel_spec(c),
{
    c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u' || c == 'A' || c == 'E' || c == 'I'
        || c == 'O' || c == 'U'
}

// Implementation following the ground-truth
// This function removes vowels from a given string
fn remove_vowels(str: &[char]) -> (str_without_vowels: Vec<char>)
    ensures
        str_without_vowels@ == str@.filter(|x: char| !is_vowel_spec(x)),
{
    let ghost str_length = str.len();
    let mut str_without_vowels: Vec<char> = Vec::new();
                                                                                       ;

    for index in 0..str.len()
                                                                                                                 
    {
        if !is_vowel(str[index]) {
            str_without_vowels.push(str[index]);
        }
                                                                                    ;
        reveal(Seq::filter);
    }
                                                ;
    str_without_vowels
}

} // verus!

fn main() {}
