use vstd::prelude::*;

fn main() {}

verus! {

spec fn is_digit(c: u8) -> bool {
    (c >= 48 && c <= 57)
}

spec fn count_digits_recursively(seq: Seq<u8>) -> int
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

fn count_digits(text: &[u8]) -> (count: usize)
    ensures
        0 <= count <= text.len(),
        count_digits_recursively(text@) == count,
{
    let mut count = 0;
    let mut index = 0;

    while index < text.len()
        invariant
            index <= text.len(),
            count <= index,
            count_digits_recursively(text@.take(index as int)) == count,
        decreases text.len() - index,
    {
        if (text[index] >= 48 && text[index] <= 57) {
            count += 1;
        }
        index += 1;

        // Prove the invariant is maintained
        assert(text@.take(index as int) =~= text@.take((index - 1) as int).push(text[(index - 1) as int])) by {
            text@.lemma_take_succ_push((index - 1) as int);
        }
        
        // Prove that the recursive definition holds
        assert(count_digits_recursively(text@.take(index as int)) == 
               count_digits_recursively(text@.take((index - 1) as int).push(text[(index - 1) as int]))) by {
            assert(text@.take(index as int).drop_last() =~= text@.take((index - 1) as int));
            assert(text@.take(index as int).last() == text[(index - 1) as int]);
        }
        
        assert(count_digits_recursively(text@.take(index as int)) == count) by {
            let prev_seq = text@.take((index - 1) as int);
            let current_char = text[(index - 1) as int];
            let current_seq = prev_seq.push(current_char);
            
            assert(current_seq.drop_last() =~= prev_seq);
            assert(current_seq.last() == current_char);
            
            assert(count_digits_recursively(current_seq) == 
                   count_digits_recursively(prev_seq) + 
                   if is_digit(current_char) { 1 as int } else { 0 as int });
                   
            if is_digit(current_char) {
                assert(count == count_digits_recursively(prev_seq) + 1);
                assert(count_digits_recursively(current_seq) == count);
            } else {
                assert(count == count_digits_recursively(prev_seq));
                assert(count_digits_recursively(current_seq) == count);
            }
        }
    }

    // Prove the postcondition
    assert(text@.take(text.len() as int) == text@) by {
        text@.lemma_take_len();
    }
    assert(count_digits_recursively(text@) == count);

    count
}

} // verus!