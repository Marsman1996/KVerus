use vstd::prelude::*;

verus! {

fn is_sub_list_at_index(main: &Vec<i32>, sub: &Vec<i32>, idx: usize) -> (result: bool)
    requires
        sub.len() <= main.len(),
        0 <= idx <= (main.len() - sub.len()),
    ensures
        result == (main@.subrange(idx as int, (idx + sub@.len())) =~= sub@),
{
    let mut i = 0;
    while i < sub.len()
        invariant
            sub.len() <= main.len(),
            0 <= idx <= (main.len() - sub.len()),
            0 <= i <= sub.len(),
            main@.subrange(idx as int, (idx + i) as int) =~= sub@.subrange(0, i as int),
        decreases sub.len() - i,
    {
        if (main[idx + i] != sub[i]) {
            assert(main@[idx + i] != sub@[i as int]);
            assert(!(main@.subrange(idx as int, (idx + sub@.len())) =~= sub@));
            return false;
        }
        i += 1;
    }
    assert(main@.subrange(idx as int, (idx + sub@.len())) =~= sub@);
    true
}

fn is_sub_list(main: &Vec<i32>, sub: &Vec<i32>) -> (result: bool)
    requires
        sub.len() <= main.len(),
    ensures
        result == (exists|k: int, l: int|
            0 <= k <= (main.len() - sub.len()) && l == k + sub.len() && (#[trigger] (main@.subrange(
                k,
                l,
            ))) =~= sub@),
{
    if sub.len() > main.len() {
        return false;
    }
    let mut index = 0;
    while index <= (main.len() - sub.len())
        invariant
            sub.len() <= main.len(),
            0 <= index <= (main.len() - sub.len()) + 1,
            forall|k: int, l: int| 0 <= k < index && l == k + sub.len() ==> !(#[trigger] (main@.subrange(k, l)) =~= sub@),
        decreases (main.len() - sub.len()) - index + 1,
    {
        if (is_sub_list_at_index(&main, &sub, index)) {
            return true;
        }
        index += 1;
    }
    false
}

fn main() {}

} // verus!