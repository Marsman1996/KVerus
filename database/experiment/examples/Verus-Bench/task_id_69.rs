use vstd::prelude::*;

fn main() {}

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
            i <= sub.len(),
            sub.len() <= main.len(),
            0 <= idx <= (main.len() - sub.len()),
            forall|j: int| 0 <= j < i ==> main@[idx as int + j] == sub@[j],
        decreases sub.len() - i,
    {
        if (main[idx + i] != sub[i]) {
            return false;
        }
        i += 1;
    }
    
    // Prove that all elements match
    assert(forall|j: int| 0 <= j < sub@.len() ==> main@[idx as int + j] == sub@[j]);
    
    // Prove the subrange equality
    assert(main@.subrange(idx as int, (idx + sub@.len())) =~= sub@) by {
        let subrange = main@.subrange(idx as int, (idx + sub@.len()));
        assert(subrange.len() == sub@.len());
        assert(forall|k: int| 0 <= k < sub@.len() ==> subrange[k] == sub@[k]) by {
            assert(forall|k: int| 0 <= k < sub@.len() ==> subrange[k] == main@[idx as int + k]);
            assert(forall|k: int| 0 <= k < sub@.len() ==> main@[idx as int + k] == sub@[k]);
        }
    }
    
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
            index <= (main.len() - sub.len()) + 1,
            sub.len() <= main.len(),
            forall|k: int| 0 <= k < index ==> {
                let l = k + sub@.len();
                !(#[trigger] main@.subrange(k, l) =~= sub@)
            },
        decreases (main.len() - sub.len()) + 1 - index,
    {
        if (is_sub_list_at_index(&main, &sub, index)) {
            assert(main@.subrange(index as int, index as int + sub@.len()) =~= sub@);
            return true;
        }
        index += 1;
    }
    
    // Prove that no valid subrange matches
    assert(forall|k: int| 0 <= k <= (main.len() - sub.len()) ==> 
           !(main@.subrange(k, k + sub@.len()) =~= sub@));
    
    false
}

} // verus!