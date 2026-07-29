use vstd::prelude::*;

fn main() {}

verus! {

spec fn is_lower_case(c: u8) -> bool {
    c >= 97 && c <= 122
}

spec fn is_upper_case(c: u8) -> bool {
    c >= 65 && c <= 90
}

spec fn count_uppercase_recursively(seq: Seq<u8>) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_uppercase_recursively(seq.drop_last()) + if is_upper_case(seq.last()) {
            1 as int
        } else {
            0 as int
        }
    }
}

proof fn lemma_count_recursive_push(seq: Seq<u8>, elem: u8)
    ensures count_uppercase_recursively(seq.push(elem)) == 
            count_uppercase_recursively(seq) + if is_upper_case(elem) { 1int } else { 0int }
    decreases seq.len(),
{
    if seq.len() == 0 {
        assert(seq.push(elem).drop_last() =~= seq);
        assert(seq.push(elem).last() == elem);
    } else {
        lemma_count_recursive_push(seq.drop_last(), elem);
        assert(seq.push(elem).drop_last() =~= seq.drop_last().push(elem)) by {
            let pushed = seq.push(elem);
            let dropped = pushed.drop_last();
            assert(dropped.len() == seq.len());
            assert(seq.drop_last().push(elem).len() == seq.len());
            assert forall |i: int| 0 <= i < seq.len() implies dropped[i] == seq.drop_last().push(elem)[i] by {
                if i < seq.len() - 1 {
                    assert(dropped[i] == pushed[i]);
                    assert(pushed[i] == seq[i]);
                    assert(seq.drop_last().push(elem)[i] == seq.drop_last()[i]);
                    assert(seq.drop_last()[i] == seq[i]);
                } else {
                    assert(i == seq.len() - 1);
                    assert(dropped[i] == pushed[i]);
                    assert(pushed[i] == seq[i]);
                    assert(seq.drop_last().push(elem)[i] == elem);
                    assert(seq[i] == seq.last());
                }
            }
        }
        assert(seq.push(elem).last() == seq.last());
    }
}

fn count_uppercase(text: &[u8]) -> (count: u64)
    ensures
        0 <= count <= text.len(),
        count_uppercase_recursively(text@) == count,
{
    let mut index = 0;
    let mut count = 0;

    while index < text.len()
        invariant
            0 <= index <= text.len(),
            0 <= count <= index,
            count_uppercase_recursively(text@.subrange(0, index as int)) == count,
        decreases text.len() - index,
    {
        if (text[index] >= 65 && text[index] <= 90) {
            count += 1;
        }
        index += 1;

        proof {
            // Prove the invariant is maintained
            assert(text@.subrange(0, index as int) =~= text@.subrange(0, (index - 1) as int).push(text[index - 1]));
            lemma_count_recursive_push(text@.subrange(0, (index - 1) as int), text[index - 1]);
            assert(count_uppercase_recursively(text@.subrange(0, index as int)) == 
                   count_uppercase_recursively(text@.subrange(0, (index - 1) as int)) + 
                   if is_upper_case(text[index - 1]) { 1int } else { 0int });
            assert(is_upper_case(text[index - 1]) == (text[index - 1] >= 65 && text[index - 1] <= 90));
        }
    }

    // Prove that the subrange covering the entire array equals the recursive count for the entire array
    assert(text@.subrange(0, text.len() as int) =~= text@);
    
    count
}

} // verus!