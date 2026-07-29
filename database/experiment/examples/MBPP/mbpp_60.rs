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

proof fn lemma_sum_to_extend(arr: Seq<i64>, index: int)
    requires
        0 <= index < arr.len(),
    ensures
        sum_to(arr.subrange(0, index + 1)) == sum_to(arr.subrange(0, index)) + arr[index],
    decreases arr.len(),
{
    let sub1 = arr.subrange(0, index + 1);
    let sub2 = arr.subrange(0, index);
    
    assert(sub1.len() == index + 1);
    assert(sub2.len() == index);
    assert(sub1.last() == arr[index]);
    assert(sub1.drop_last() =~= sub2);
}

fn sum_range_list(arr: &Vec<i64>, start: usize, end: usize) -> (sum: i128)
    requires
        0 <= start <= end,
        start <= end < arr.len(),
    ensures
        sum_to(arr@.subrange(start as int, end + 1 as int)) == sum,
{
    let mut index = start;
    let mut sum = 0i128;
    let _end = end + 1;

    while index < _end
        invariant
            0 <= start <= end,
            start <= end < arr.len(),
            start <= index <= _end,
            _end == end + 1,
            sum == sum_to(arr@.subrange(start as int, index as int)),
            forall |i: int| start <= i < index ==> #[trigger] arr@[i] >= i128::MIN && #[trigger] arr@[i] <= i128::MAX,
            i128::MIN <= sum <= i128::MAX,
            forall |i: int| start <= i < _end ==> #[trigger] arr@[i] >= i128::MIN && #[trigger] arr@[i] <= i128::MAX,
            forall |i: int| start <= i <= index && i < _end ==> #[trigger] sum_to(arr@.subrange(start as int, i + 1)) >= i128::MIN && #[trigger] sum_to(arr@.subrange(start as int, i + 1)) <= i128::MAX,
        decreases _end - index,
    {
        proof {
            lemma_sum_to_extend(arr@.subrange(start as int, _end as int), (index - start) as int);
            assert(arr@.subrange(start as int, _end as int)[(index - start) as int] == arr@[index as int]);
            assert(arr@.subrange(start as int, index as int) =~= arr@.subrange(start as int, _end as int).subrange(0, (index - start) as int));
            assert(arr@.subrange(start as int, index + 1 as int) =~= arr@.subrange(start as int, _end as int).subrange(0, (index - start + 1) as int));
        }
        sum = sum + arr[index] as i128;
        index += 1;
    }
    sum
}

fn main() {}

} // verus!