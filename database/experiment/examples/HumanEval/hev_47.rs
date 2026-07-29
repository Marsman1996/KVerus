use vstd::prelude::*;

verus! {

pub closed spec fn concat_helper(strings: Seq<Seq<char>>, i: nat) -> Seq<char>
    recommends
        i <= strings.len(),
    decreases strings.len() - i,
{
    if (i >= strings.len()) {
        seq![]
    } else {
        strings[i as int] + concat_helper(strings, i + 1)
    }
}

pub open spec fn concatenate(strings: Seq<Seq<char>>) -> Seq<char> {
    concat_helper(strings, 0)
}

proof fn sanity_check() {
    assert(concatenate(seq![seq!['a'], seq!['b'], seq!['c']]) == seq!['a', 'b', 'c']) by (compute);
                                                             ;
    assert(concatenate(seq![seq!['a', 'z'], seq!['b'], seq!['c', 'y']]) == seq![
        'a',
        'z',
        'b',
        'c',
        'y',
    ]) by (compute);
}

proof fn concat_helper_append_lemma(strings: Seq<Seq<char>>, i: nat)
    requires
        i < strings.len(),
    ensures
        concat_helper(strings, i) == strings[i as int] + concat_helper(strings, i + 1),
    decreases strings.len() - i,
{
}

proof fn concat_helper_prefix_lemma(strings: Seq<Seq<char>>, i: nat, j: nat)
    requires
        i <= j,
        j <= strings.len(),
    ensures
        concat_helper(strings, i) == concat_helper(strings, i).subrange(0, concat_helper(strings, i).len() as int - concat_helper(strings, j).len() as int) + concat_helper(strings, j),
        concat_helper(strings, i).len() >= concat_helper(strings, j).len(),
    decreases j - i,
{
    if i < j {
        concat_helper_append_lemma(strings, i);
        concat_helper_prefix_lemma(strings, i + 1, j);
        assert(concat_helper(strings, i) == strings[i as int] + concat_helper(strings, i + 1));
        assert(concat_helper(strings, i + 1) == concat_helper(strings, i + 1).subrange(0, concat_helper(strings, i + 1).len() as int - concat_helper(strings, j).len() as int) + concat_helper(strings, j));
    }
}

fn concatenate_impl(strings: Vec<Vec<char>>) -> (joined: Vec<char>)
    ensures
        joined@ == concatenate(strings.deep_view()),
{
    let mut i = 0;
    let mut joined = vec![];

    while (i < strings.len())
        invariant
            i <= strings.len(),
            joined@ == concat_helper(strings.deep_view(), 0).subrange(0, concat_helper(strings.deep_view(), 0).len() as int - concat_helper(strings.deep_view(), i as nat).len() as int),
            concat_helper(strings.deep_view(), 0).len() >= concat_helper(strings.deep_view(), i as nat).len(),
        decreases strings.len() - i,
    {
        proof {
            concat_helper_append_lemma(strings.deep_view(), i as nat);
            concat_helper_prefix_lemma(strings.deep_view(), 0, i as nat);
            concat_helper_prefix_lemma(strings.deep_view(), 0, (i + 1) as nat);
        }
        
        let mut copy_str = strings[i].clone();
        joined.append(&mut copy_str);
        i = i + 1;
    }
    return joined;
}

} // verus!
fn main() {
    let test1 = vec![vec!['a'], vec!['b'], vec!['c']];
    let test2: Vec<Vec<char>> = Vec::new();
    let test3 = vec![vec!['a', 'z'], vec!['b'], vec!['c', 'y']];

    print!("concatenation of {:?}:\n", test1);
    print!("{:?}\n", concatenate_impl(test1));
    print!("concatenation of {:?}:\n", test2);
    print!("{:?}\n", concatenate_impl(test2));
    print!("concatenation of {:?}:\n", test3);
    print!("{:?}\n", concatenate_impl(test3));
}

/*
### VERUS END
*/

/*
### PROMPT
from typing import List


def concatenate(strings: List[str]) -> str:
    """ Concatenate list of strings into a single string
    >>> concatenate([])
    ''
    >>> concatenate(['a', 'b', 'c'])
    'abc'
    """

*/

/*
### ENTRY POINT
concatenate
*/

/*
### CANONICAL SOLUTION
    return ''.join(strings)

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([]) == ''
    assert candidate(['x', 'y', 'z']) == 'xyz'
    assert candidate(['x', 'y', 'z', 'w', 'k']) == 'xyzwk'

*/