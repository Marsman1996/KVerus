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
                                   ;
                                                       ;
    } else if s.len() > 1 {
        let ss = s.skip(1);
        lemma_sum_equals_sum_other_way(ss);
                                                                                            ;
        lemma_sum_equals_sum_other_way(ss.take(ss.len() - 1));
                                                                    ;
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
        invariant
            s == sum(operations@.take(k as int).map(|_idx, j: i32| j as int)),
            forall|i: int|
                0 <= i <= operations@.len() ==> sum(
                    operations@.take(i).map(|_idx, j: i32| j as int),
                ) <= i32::MAX,
            forall|i: int|
                0 <= i <= k ==> sum(operations@.take(i).map(|_idx, j: i32| j as int)) >= 0,
    {
        assert(s + operations@[k as int] == sum(
            operations@.take(k + 1).map(|_idx, j: i32| j as int),
        )) by {
            let q1 = operations@.take(k as int).map(|_idx, j: i32| j as int);
            let q2 = operations@.take(k + 1).map(|_idx, j: i32| j as int);
            assert(q2[q2.len() - 1] == operations@[k as int] as int);
            assert(q2.take(q2.len() - 1) == q1);
            lemma_sum_equals_sum_other_way(q1);
            lemma_sum_equals_sum_other_way(q2);
        }
        s = s + operations[k];
        if s < 0 {
            return true;
        }
    }
    false
}

} // verus!

fn main() {}
