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
    if s.len() == 0 {
        // Base case: both are 0
    } else if s.len() == 1 {
        assert(s.skip(1).len() == 0);
        assert(s.take(0).len() == 0);
    } else if s.len() > 1 {
        let ss = s.skip(1);
        lemma_sum_equals_sum_other_way(ss);
        assert(sum(ss) == sum_other_way(ss));
        lemma_sum_equals_sum_other_way(ss.take(ss.len() - 1));
        assert(ss.take(ss.len() - 1) == s.skip(1).take(s.len() - 2));
        lemma_sum_equals_sum_other_way(s.take(s.len() - 1));
        // Need to show: s[0] + sum(ss) == s[s.len()-1] + sum_other_way(s.take(s.len()-1))
        // We know: sum(ss) == sum_other_way(ss)
        // We know: sum(s.take(s.len()-1)) == sum_other_way(s.take(s.len()-1))
        // s.take(s.len()-1) is s without the last element
        // ss is s without the first element
        // sum_other_way(s.take(s.len()-1)) = s[s.len()-2] + sum_other_way(s.take(s.len()-2))
        // sum(s.take(s.len()-1)) = s[0] + sum(s.take(s.len()-1).skip(1))
        // s.take(s.len()-1).skip(1) = ss.take(ss.len()-1)
        assert(s.take(s.len() - 1).skip(1) =~= ss.take(ss.len() - 1));
        assert(sum(s.take(s.len() - 1)) == s[0] + sum(s.take(s.len() - 1).skip(1)));
        assert(sum(s.take(s.len() - 1).skip(1)) == sum(ss.take(ss.len() - 1)));
        assert(s.take(s.len() - 1).len() == s.len() - 1);
        assert(s.take(s.len() - 1).take(s.len() - 2) =~= s.take(s.len() - 2));
        assert(ss.take(ss.len() - 1) =~= s.skip(1).take(s.len() - 2));
        assert(forall|i: int| #![trigger s.skip(1).take(s.len() - 2)[i]] 0 <= i < s.len() - 2 ==> s.skip(1).take(s.len() - 2)[i] == s[i + 1]);
        assert(forall|i: int| #![trigger s.take(s.len() - 1).take(s.len() - 2)[i]] 0 <= i < s.len() - 2 ==> s.take(s.len() - 1).take(s.len() - 2)[i] == s[i]);
        assert(sum_other_way(s.take(s.len() - 1)) == s.take(s.len() - 1)[s.take(s.len() - 1).len() - 1] + sum_other_way(s.take(s.len() - 1).take(s.take(s.len() - 1).len() - 1)));
        assert(s.take(s.len() - 1)[s.take(s.len() - 1).len() - 1] == s[s.len() - 2]);
        assert(sum(ss.take(ss.len() - 1)) == sum_other_way(ss.take(ss.len() - 1)));
        assert(sum_other_way(ss) == ss[ss.len() - 1] + sum_other_way(ss.take(ss.len() - 1)));
        assert(ss[ss.len() - 1] == s[s.len() - 1]);
        assert(sum(ss) == ss[0] + sum(ss.skip(1)));
        assert(sum(s) == s[0] + sum(ss));
        assert(sum(s) == s[0] + sum_other_way(ss));
        assert(sum_other_way(s) == s[s.len() - 1] + sum_other_way(s.take(s.len() - 1)));
        assert(sum(s.take(s.len() - 1)) == sum_other_way(s.take(s.len() - 1)));
        assert(sum(s.take(s.len() - 1)) == s[0] + sum(ss.take(ss.len() - 1)));
        assert(forall|i: int| 0 <= i < s.len() - 2 ==> s.take(s.len() - 1).take(s.take(s.len() - 1).len() - 1)[i] == ss.take(ss.len() - 1)[i]);
        assert(s.take(s.len() - 1).take(s.take(s.len() - 1).len() - 1).len() == ss.take(ss.len() - 1).len());
        assert(s.take(s.len() - 1).take(s.take(s.len() - 1).len() - 1) =~= ss.take(ss.len() - 1));
        assert(sum_other_way(s.take(s.len() - 1)) == s[s.len() - 2] + sum_other_way(ss.take(ss.len() - 1)));
        assert(ss.len() == s.len() - 1);
        assert(ss[ss.len() - 1] == s[s.len() - 1]);
        assert(ss.len() >= 2);
        assert(ss[ss.len() - 2] == s[s.len() - 2]);
        assert(sum_other_way(s.take(s.len() - 1)) == ss[ss.len() - 2] + sum_other_way(ss.take(ss.len() - 1)));
        assert(sum_other_way(ss) == ss[ss.len() - 1] + ss[ss.len() - 2] + sum_other_way(ss.take(ss.len() - 1)));
        assert(sum_other_way(s.take(s.len() - 1)) == sum_other_way(ss) - ss[ss.len() - 1]);
        assert(sum(s) == s[0] + sum_other_way(ss));
        assert(sum_other_way(s) == s[s.len() - 1] + sum_other_way(s.take(s.len() - 1)));
        assert(s[0] == s.take(s.len() - 1)[0]);
        assert(s[s.len() - 1] == ss[ss.len() - 1]);
        assert(sum(s.take(s.len() - 1)) == s[0] + sum_other_way(ss.take(ss.len() - 1)));
        assert(sum_other_way(ss) == ss[ss.len() - 1] + sum_other_way(ss.take(ss.len() - 1)));
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