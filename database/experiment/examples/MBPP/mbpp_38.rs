use vstd::prelude::*;

verus! {

spec fn count_identical(s1: Seq<i32>, s2: Seq<i32>, s3: Seq<i32>) -> int
    decreases s1.len(), s2.len(), s3.len(),
{
    if s1.len() == 0 || s2.len() == 0 || s3.len() == 0 {
        0
    } else {
        count_identical(s1.drop_last(), s2.drop_last(), s3.drop_last()) + if (s1.last() == s2.last()
            && s2.last() == s3.last()) {
            1 as int
        } else {
            0 as int
        }
    }
}

proof fn lemma_count_identical_take(s1: Seq<i32>, s2: Seq<i32>, s3: Seq<i32>, i: int)
    requires
        s1.len() == s2.len() && s2.len() == s3.len(),
        0 <= i < s1.len(),
    ensures
        count_identical(s1.take(i + 1), s2.take(i + 1), s3.take(i + 1)) ==
            count_identical(s1.take(i), s2.take(i), s3.take(i)) +
            if s1[i] == s2[i] && s2[i] == s3[i] { 1int } else { 0int },
{
    assert(s1.take(i + 1).len() == i + 1);
    assert(s2.take(i + 1).len() == i + 1);
    assert(s3.take(i + 1).len() == i + 1);
    assert(s1.take(i + 1).last() == s1[i]);
    assert(s2.take(i + 1).last() == s2[i]);
    assert(s3.take(i + 1).last() == s3[i]);
    assert(s1.take(i + 1).drop_last() =~= s1.take(i));
    assert(s2.take(i + 1).drop_last() =~= s2.take(i));
    assert(s3.take(i + 1).drop_last() =~= s3.take(i));
}

proof fn lemma_count_identical_full(s1: Seq<i32>, s2: Seq<i32>, s3: Seq<i32>)
    requires
        s1.len() == s2.len() && s2.len() == s3.len(),
    ensures
        count_identical(s1.take(s1.len() as int), s2.take(s2.len() as int), s3.take(s3.len() as int)) ==
            count_identical(s1, s2, s3),
{
    assert(s1.take(s1.len() as int) =~= s1);
    assert(s2.take(s2.len() as int) =~= s2);
    assert(s3.take(s3.len() as int) =~= s3);
}

fn count_identical_position(arr1: &Vec<i32>, arr2: &Vec<i32>, arr3: &Vec<i32>) -> (count: usize)
    requires
        arr1.len() == arr2.len() && arr2.len() == arr3.len(),
    ensures
        0 <= count <= arr1.len(),
        count_identical(arr1@, arr2@, arr3@) == count,
{
    let mut count = 0;
    let mut index = 0;
    while index < arr1.len()
        invariant
            arr1.len() == arr2.len() && arr2.len() == arr3.len(),
            index <= arr1.len(),
            0 <= count <= index,
            count == count_identical(arr1@.take(index as int), arr2@.take(index as int), arr3@.take(index as int)),
        decreases arr1.len() - index,
    {
        if arr1[index] == arr2[index] && arr2[index] == arr3[index] {
            count += 1;
            proof {
                lemma_count_identical_take(arr1@, arr2@, arr3@, index as int);
            }
        } else {
            proof {
                lemma_count_identical_take(arr1@, arr2@, arr3@, index as int);
            }
        }
        index += 1;
    }
    proof {
        lemma_count_identical_full(arr1@, arr2@, arr3@);
    }
    count
}

fn main() {}

} // verus!