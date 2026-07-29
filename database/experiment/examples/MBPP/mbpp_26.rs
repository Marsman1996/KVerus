use vstd::prelude::*;

verus! {

spec fn is_digit(c: char) -> bool {
    (c as u8) >= 48 && (c as u8) <= 57
}

spec fn count_digits_recursively(seq: Seq<char>) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_digits_recursively(seq.drop_last()) + if is_digit(seq.last()) {
            1 as int
        } else {
            0 as int
        }
    }
}

proof fn lemma_count_digits_push(seq: Seq<char>, c: char)
    ensures
        count_digits_recursively(seq.push(c)) == 
            count_digits_recursively(seq) + if is_digit(c) { 1 as int } else { 0 as int }
{
    assert(seq.push(c).drop_last() =~= seq);
    assert(seq.push(c).last() == c);
}

fn count_digits(text: &Vec<char>) -> (count: usize)
    ensures
        0 <= count <= text.len(),
        count_digits_recursively(text@) == count,
{
    let mut count = 0;

    let mut index = 0;
    while index < text.len()
        invariant
            0 <= index <= text.len(),
            0 <= count <= index,
            count_digits_recursively(text@.take(index as int)) == count,
        decreases text.len() - index,
    {
        if ((text[index] as u8) >= 48 && (text[index] as u8) <= 57) {
            count += 1;
        }
        index += 1;
        assert(text@.take(index as int) == text@.take((index - 1) as int).push(text@[index - 1]));
        proof {
            let prev_index = (index - 1) as int;
            let curr_index = index as int;
            assert(text@.take(curr_index) == text@.take(prev_index).push(text@[prev_index]));
            lemma_count_digits_push(text@.take(prev_index), text@[prev_index]);
            assert(count_digits_recursively(text@.take(prev_index).push(text@[prev_index])) == 
                   count_digits_recursively(text@.take(prev_index)) + if is_digit(text@[prev_index]) { 1 as int } else { 0 as int });
        }
    }
    assert(text@.take(index as int) == text@);
    count
}

fn main() {}

} // verus!