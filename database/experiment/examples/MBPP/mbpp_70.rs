use vstd::prelude::*;

verus! {

spec fn count_boolean(seq: Seq<bool>) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_boolean(seq.drop_last()) + if (seq.last()) {
            1 as int
        } else {
            0 as int
        }
    }
}

proof fn lemma_count_boolean_subrange(arr: Seq<bool>, i: int)
    requires
        0 <= i < arr.len(),
    ensures
        count_boolean(arr.subrange(0, i + 1)) == count_boolean(arr.subrange(0, i)) + if arr[i] { 1int } else { 0int },
{
    assert(arr.subrange(0, i + 1) =~= arr.subrange(0, i).push(arr[i]));
    lemma_count_boolean_push(arr.subrange(0, i), arr[i]);
}

proof fn lemma_count_boolean_push(seq: Seq<bool>, b: bool)
    ensures
        count_boolean(seq.push(b)) == count_boolean(seq) + if b { 1int } else { 0int },
{
    assert(seq.push(b).drop_last() =~= seq);
    assert(seq.push(b).last() == b);
}

fn count_true(arr: &Vec<bool>) -> (count: u64)
    ensures
        0 <= count <= arr.len(),
        count_boolean(arr@) == count,
{
    let mut index = 0;
    let mut counter = 0;

    while index < arr.len()
        invariant
            0 <= index <= arr.len(),
            0 <= counter <= index,
            count_boolean(arr@.subrange(0, index as int)) == counter,
        decreases arr.len() - index,
    {
        proof {
            lemma_count_boolean_subrange(arr@, index as int);
        }
        if (arr[index]) {
            counter += 1;
        }
        index += 1;
    }
    assert(arr@.subrange(0, index as int) =~= arr@);
    counter
}

fn main() {}

} // verus!