use vstd::prelude::*;

verus! {

// This function is part of the specification
pub open spec fn sum(s: Seq<int>) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] + sum(s.skip(1))
    }
}

// This function is used by the proof
pub open spec fn sum_other_way(s: Seq<int>) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[s.len() - 1] + sum_other_way(s.take(s.len() - 1))
    }
}

proof fn lemma_sum_equals_sum_other_way(s: Seq<int>)
    ensures
        sum(s) == sum_other_way(s),
    decreases s.len(),
{
    if s.len() == 1 {
        assert(sum(s.skip(1)) == 0);
        assert(sum_other_way(s.take(s.len() - 1)) == 0);
    } else if s.len() > 1 {
        let ss = s.skip(1);
        lemma_sum_equals_sum_other_way(ss);
        assert(sum_other_way(ss) == ss[ss.len() - 1] + sum_other_way(ss.take(ss.len() - 1)));
        lemma_sum_equals_sum_other_way(ss.take(ss.len() - 1));
        assert(ss.take(ss.len() - 1) == s.take(s.len() - 1).skip(1));
        lemma_sum_equals_sum_other_way(s.take(s.len() - 1));
    }
}

fn below_zero(operations: Vec<i32>) -> (result: bool)
    requires
        forall|i: int|
            0 <= i <= operations@.len() ==> sum(operations@.take(i).map(|_idx, j: i32| j as int))
                <= i32::MAX,
    ensures
        result <==> exists|i: int|
            0 <= i <= operations@.len() && sum(operations@.take(i).map(|_idx, j: i32| j as int))
                < 0,
{
    let mut s = 0i32;
    for k in 0..operations.len()
                                                                                                                                                                                                                                                                                                                                                                                                            
    {
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
        s = s + operations[k];
        if s < 0 {
            return true;
        }
    }
    false
}

} // verus!

fn main() {}
