use vstd::prelude::*;

verus! {

spec fn sum_to(arr: Seq<i64>) -> int
    decreases arr.len(),
{
    if arr.len() == 0 {
        0
    } else {
        sum_to(arr.drop_last()) + arr.last()
    }
}

proof fn lemma_sum_to_subrange(arr: Seq<i64>, i: int)
    requires
        0 <= i < arr.len(),
    ensures
        sum_to(arr.subrange(0, i + 1)) == sum_to(arr.subrange(0, i)) + arr[i],
{
    assert(arr.subrange(0, i + 1).drop_last() =~= arr.subrange(0, i));
    assert(arr.subrange(0, i + 1).last() == arr[i]);
}

proof fn lemma_sum_bounds(arr: Seq<i64>, i: int)
    requires
        0 <= i < arr.len(),
        sum_to(arr) >= i128::MIN,
        sum_to(arr) <= i128::MAX,
        sum_to(arr.subrange(0, i)) >= i128::MIN,
        sum_to(arr.subrange(0, i)) <= i128::MAX,
    ensures
        sum_to(arr.subrange(0, i)) + arr[i] >= i128::MIN,
        sum_to(arr.subrange(0, i)) + arr[i] <= i128::MAX,
{
    lemma_sum_to_subrange(arr, i);
    assert(sum_to(arr.subrange(0, i + 1)) == sum_to(arr.subrange(0, i)) + arr[i]);
    lemma_sum_to_subrange_bounds(arr, i);
}

proof fn lemma_sum_to_subrange_bounds(arr: Seq<i64>, i: int)
    requires
        0 <= i < arr.len(),
        sum_to(arr) >= i128::MIN,
        sum_to(arr) <= i128::MAX,
    ensures
        sum_to(arr.subrange(0, i + 1)) >= i128::MIN,
        sum_to(arr.subrange(0, i + 1)) <= i128::MAX,
{
    if i + 1 == arr.len() {
        assert(arr.subrange(0, i + 1) =~= arr);
    } else {
        lemma_sum_to_subrange_bounds_helper(arr, i + 1);
    }
}

proof fn lemma_sum_to_subrange_bounds_helper(arr: Seq<i64>, j: int)
    requires
        0 < j <= arr.len(),
        sum_to(arr) >= i128::MIN,
        sum_to(arr) <= i128::MAX,
    ensures
        sum_to(arr.subrange(0, j)) >= i128::MIN,
        sum_to(arr.subrange(0, j)) <= i128::MAX,
    decreases j,
{
    if j == arr.len() {
        assert(arr.subrange(0, j) =~= arr);
    }
}

fn sum(arr: &Vec<i64>) -> (sum: i128)
    requires
        sum_to(arr@) >= i128::MIN,
        sum_to(arr@) <= i128::MAX,
    ensures
        sum_to(arr@) == sum,
{
    let mut index = 0;
    let mut sum = 0i128;

    while index < arr.len()
        invariant
            index <= arr.len(),
            sum == sum_to(arr@.subrange(0, index as int)),
            sum_to(arr@) >= i128::MIN,
            sum_to(arr@) <= i128::MAX,
            sum >= i128::MIN,
            sum <= i128::MAX,
            forall|j: int| 0 <= j <= index ==> sum_to(arr@.subrange(0, j)) >= i128::MIN,
            forall|j: int| 0 <= j <= index ==> sum_to(arr@.subrange(0, j)) <= i128::MAX,
        decreases arr.len() - index,
    {
        proof {
            lemma_sum_bounds(arr@, index as int);
            lemma_sum_to_subrange_bounds(arr@, index as int);
        }
        sum = sum + arr[index] as i128;
        index += 1;
        proof {
            assert forall|j: int| 0 <= j <= index implies sum_to(arr@.subrange(0, j)) >= i128::MIN by {
                if j < index {
                } else {
                    lemma_sum_to_subrange_bounds(arr@, (index - 1) as int);
                }
            }
            assert forall|j: int| 0 <= j <= index implies sum_to(arr@.subrange(0, j)) <= i128::MAX by {
                if j < index {
                } else {
                    lemma_sum_to_subrange_bounds(arr@, (index - 1) as int);
                }
            }
        }
    }
    assert(arr@.subrange(0, index as int) =~= arr@);
    sum
}

fn main() {}

} // verus!