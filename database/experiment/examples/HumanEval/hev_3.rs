use vstd::prelude::*;

verus! {

/// This function computes the net nesting level at the end of a particular `input`,
/// where a left parenthesis increments the net nesting level and a right parenthesis
/// decrements it.
pub open spec fn nesting_level(input: Seq<char>) -> int
    decreases input.len(),
{
    if input.len() == 0 {
        0
    } else {
        let prev_nesting_level = nesting_level(input.drop_last());
        let c = input.last();
        if c == '(' {
            prev_nesting_level + 1
        } else if c == ')' {
            prev_nesting_level - 1
        } else {
            prev_nesting_level
        }
    }
}

pub open spec fn is_paren_char(c: char) -> bool {
    c == '(' || c == ')'
}

/// A sequence of characters is a balanced group of parentheses if
/// it's non-empty, it only consists of parentheses, its nesting level
/// is zero, and any nonempty strict prefix has a positive nesting
/// level.
pub open spec fn is_balanced_group(input: Seq<char>) -> bool {
    &&& input.len() > 0
    &&& nesting_level(input) == 0
    &&& forall|i| 0 <= i < input.len() ==> is_paren_char(#[trigger] input[i])
    &&& forall|i| 0 < i < input.len() ==> nesting_level(#[trigger] input.take(i)) > 0
}

/// A sequence of characters is a sequence of balanced groups of
/// parentheses if its nesting level is zero and any prefix has
/// a non-negative nesting level.
pub open spec fn is_sequence_of_balanced_groups(input: Seq<char>) -> bool {
    &&& nesting_level(input) == 0
    &&& forall|i| 0 < i < input.len() ==> nesting_level(#[trigger] input.take(i)) >= 0
}

pub open spec fn vecs_to_seqs<T>(s: Seq<Vec<T>>) -> Seq<Seq<T>> {
    s.map(|_i, ss: Vec<T>| ss@)
}

pub open spec fn remove_nonparens(s: Seq<char>) -> Seq<char> {
    s.filter(|c| is_paren_char(c))
}

/// This proof specifies the relationship between `remove_nonparens(s.take(pos + 1))`
/// and `remove_nonparens(s.take(pos))`.
proof fn lemma_remove_nonparens_maintained_by_push(s: Seq<char>, pos: int)
    requires
        0 <= pos < s.len(),
    ensures
        ({
            let s1 = remove_nonparens(s.take(pos as int));
            let s2 = remove_nonparens(s.take((pos + 1) as int));
            if is_paren_char(s[pos]) {
                s2 == s1.push(s[pos])
            } else {
                s2 == s1
            }
        }),
    decreases pos,
{
    reveal(Seq::filter);
    assert(s.take((pos + 1) as int).drop_last() =~= s.take(pos as int));
    if pos != 0 {
        lemma_remove_nonparens_maintained_by_push(s, pos - 1);
    }
}

proof fn lemma_nesting_level_add(s1: Seq<char>, s2: Seq<char>)
    ensures
        nesting_level(s1 + s2) == nesting_level(s1) + nesting_level(s2),
    decreases s2.len(),
{
    if s2.len() == 0 {
        assert(s1 + s2 =~= s1);
    } else {
        lemma_nesting_level_add(s1, s2.drop_last());
        assert((s1 + s2).drop_last() =~= s1 + s2.drop_last());
    }
}

/// This is the function specified at the top of the file.
fn separate_paren_groups(input: &Vec<char>) -> (groups: Vec<Vec<char>>)
    requires
        is_sequence_of_balanced_groups(input@),
    ensures
// All groups in the result are balanced and non-nested

        forall|i: int|
            #![trigger groups[i]]
            0 <= i < groups.len() ==> is_balanced_group(groups[i]@),
        // The concatenation of all groups in the result equals the input string without spaces
        vecs_to_seqs(groups@).flatten() == remove_nonparens(input@),
{
    // Loop through the input one character at a time, keeping track of:
    //
    // `groups`: A vector of complete balanced groups found so far.
    // `current_group`: The current, incomplete balanced group found since then.
    let mut groups: Vec<Vec<char>> = Vec::new();
    let mut current_group: Vec<char> = Vec::new();
    let input_len = input.len();
    // For proof purposes, we also keep track of some ghost state that
    // lets us more readily reason about
    // `vecs_to_seqs(groups@)`. Specifically, we'll maintain
    // the invariant that `ghost_groups == vecs_to_seqs(groups@)`.
    let ghost mut ghost_groups: Seq<Seq<char>> = Seq::empty();
    proof {
        assert(ghost_groups == vecs_to_seqs(groups@));
        assert(ghost_groups.flatten() == remove_nonparens(input@.take(0)));
        assert(nesting_level(current_group@) == 0);
    }
    let mut current_nesting_level: usize = 0;
    for pos in 0..input_len
        invariant
            is_sequence_of_balanced_groups(input@),
            0 <= pos <= input_len,
            input_len == input@.len(),
            ghost_groups == vecs_to_seqs(groups@),
            ghost_groups.flatten() + current_group@ == remove_nonparens(input@.take(pos as int)),
            current_nesting_level == nesting_level(current_group@),
            nesting_level(current_group@) >= 0,
            current_nesting_level < usize::MAX,
            forall|i: int| 0 <= i < groups@.len() ==> is_balanced_group(#[trigger] groups@[i]@),
            forall|i: int| 0 < i < current_group@.len() ==> nesting_level(#[trigger] current_group@.take(i)) > 0,
            nesting_level(ghost_groups.flatten()) == 0,
    {
        let ghost prev_group = current_group@;
        let ghost prev_groups = ghost_groups;
        let c = input[pos];
        proof {
            assert(input@.take((pos + 1) as int).drop_last() =~= input@.take(pos as int));
            assert(0 <= pos < input@.len());
            lemma_remove_nonparens_maintained_by_push(input@, pos as int);
        }
        if c == '(' {
            current_nesting_level = current_nesting_level + 1;
            current_group.push('(');
            proof {
                assert(current_group@ == prev_group.push('('));
                assert forall|i: int| 0 < i < current_group@.len() implies nesting_level(#[trigger] current_group@.take(i)) > 0 by {
                    if i < prev_group.len() {
                        assert(current_group@.take(i) =~= prev_group.take(i));
                    } else {
                        assert(i == prev_group.len());
                        assert(current_group@.take(i) =~= prev_group);
                        assert(nesting_level(prev_group) >= 0);
                    }
                }
            }
        } else if c == ')' {
            proof {
                assert(is_sequence_of_balanced_groups(input@));
                assert(nesting_level(input@.take((pos + 1) as int)) >= 0);
                assert(ghost_groups.flatten() + prev_group == remove_nonparens(input@.take(pos as int)));
                lemma_nesting_level_add(ghost_groups.flatten(), prev_group);
                assert(nesting_level(ghost_groups.flatten() + prev_group) == nesting_level(ghost_groups.flatten()) + nesting_level(prev_group));
                assert(nesting_level(ghost_groups.flatten()) == 0);
                assert(nesting_level(ghost_groups.flatten() + prev_group) == nesting_level(prev_group));
                
                let filtered_pos = remove_nonparens(input@.take(pos as int));
                let filtered_pos_plus_1 = remove_nonparens(input@.take((pos + 1) as int));
                assert(filtered_pos_plus_1 == filtered_pos.push(')'));
                assert(filtered_pos == ghost_groups.flatten() + prev_group);
                assert(filtered_pos_plus_1 == ghost_groups.flatten() + prev_group.push(')'));
                
                assert((ghost_groups.flatten() + prev_group.push(')')).drop_last() =~= ghost_groups.flatten() + prev_group);
                assert(nesting_level(ghost_groups.flatten() + prev_group.push(')')) == nesting_level(ghost_groups.flatten() + prev_group) - 1);
                assert(nesting_level(filtered_pos_plus_1) == nesting_level(prev_group) - 1);
                assert(nesting_level(prev_group.push(')')) == nesting_level(prev_group) - 1);
                assert(nesting_level(prev_group) >= 1);
                assert(current_nesting_level >= 1);
            }
            current_nesting_level = current_nesting_level - 1;
            current_group.push(')');
            proof {
                assert(current_group@ == prev_group.push(')'));
                assert forall|i: int| 0 < i < current_group@.len() implies nesting_level(#[trigger] current_group@.take(i)) > 0 by {
                    if i < prev_group.len() {
                        assert(current_group@.take(i) =~= prev_group.take(i));
                    } else if i == prev_group.len() {
                        assert(current_group@.take(i) =~= prev_group);
                    } else {
                        assert(false);
                    }
                }
            }
            // We can tell whether the current group we just assembled is balanced
            // by checking whether `current_nesting_level` is zero. In that case,
            // it's done and we can add it to `groups`.
            if current_nesting_level == 0 {
                proof {
                    ghost_groups = ghost_groups.push(current_group@);
                    assert(is_balanced_group(current_group@));
                    ghost_groups.lemma_flatten_push(current_group@);
                    assert(ghost_groups.flatten() == prev_groups.flatten() + current_group@);
                    lemma_nesting_level_add(prev_groups.flatten(), current_group@);
                }
                groups.push(current_group);
                current_group = Vec::<char>::new();
                proof {
                    assert(current_group@ == Seq::<char>::empty());
                }
            }
        }
    }
    proof {
        assert(input@.take(input_len as int) =~= input@);
        assert(ghost_groups.flatten() + current_group@ == remove_nonparens(input@));
        lemma_nesting_level_add(ghost_groups.flatten(), current_group@);
        assert(nesting_level(remove_nonparens(input@)) == nesting_level(ghost_groups.flatten()) + nesting_level(current_group@));
        assert(nesting_level(ghost_groups.flatten()) == 0);
        assert(nesting_level(remove_nonparens(input@)) == nesting_level(current_group@));
        assert(remove_nonparens(input@) =~= input@);
        assert(nesting_level(input@) == 0);
        assert(nesting_level(current_group@) == 0);
        assert(current_nesting_level == 0);
        if current_group@.len() > 0 {
            assert(nesting_level(current_group@.take(current_group@.len() as int)) > 0);
            assert(current_group@.take(current_group@.len() as int) =~= current_group@);
            assert(false);
        }
        assert(current_group@.len() == 0);
    }
    groups
}

} // verus!

fn main() {}