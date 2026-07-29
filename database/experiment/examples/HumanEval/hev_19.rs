use vstd::prelude::*;
use vstd::assert_seqs_equal;

verus! {

/// Specification for what it means to sum a sequence of numbers
pub open spec fn sum(numbers: Seq<u32>) -> int {
    numbers.fold_left(0, |acc: int, x| acc + x)
}

/// Specification for taking the product of a sequence of numbers
pub open spec fn product(numbers: Seq<u32>) -> int {
    numbers.fold_left(1, |acc: int, x| acc * x)
}

/// Show that the sum won't grow too large
proof fn sum_bound(numbers: Seq<u32>)
    ensures
        sum(numbers) <= numbers.len() * u32::MAX,
    decreases numbers.len(),
{
    if numbers.len() == 0 {
    } else {
        sum_bound(numbers.drop_last());
    }
}

/// Implementation.  We leave the consequences of an intermediate
/// overflow during the product calculation underspecified.
fn sum_product(numbers: Vec<u32>) -> (result: (u64, Option<u32>))
    requires
        numbers.len() < u32::MAX,
    ensures
        result.0 == sum(numbers@),
        match result.1 {
            None =>   // Computing the product overflowed at some point
            exists|i|
                #![auto]
                0 <= i < numbers.len() && product(numbers@.subrange(0, i)) * numbers[i as int] as int
                    > u32::MAX,
            Some(v) => v == product(numbers@),
        },
{
    let mut sum_value: u64 = 0;
    let mut prod_value: Option<u32> = Some(1);
    for index in 0..numbers.len()
        invariant
            numbers.len() < u32::MAX,
            0 <= index <= numbers.len(),
            sum_value == sum(numbers@.take(index as int)),
            match prod_value {
                None => exists|i| #![auto] 0 <= i < index && product(numbers@.subrange(0, i)) * numbers[i as int] as int > u32::MAX,
                Some(v) => v == product(numbers@.take(index as int)),
            },
    {
        proof {
            sum_bound(numbers@.take(index as int));
            assert(sum(numbers@.take(index as int)) <= numbers@.take(index as int).len() * u32::MAX);
            assert(sum(numbers@.take(index as int)) <= index as int * u32::MAX);
            assert(sum(numbers@.take(index as int)) + numbers[index as int] as int <= index as int * u32::MAX + u32::MAX);
            assert(sum(numbers@.take(index as int)) + numbers[index as int] as int <= u64::MAX);
            assert_seqs_equal!(numbers@.take((index + 1) as int) == numbers@.take(index as int).push(numbers[index as int]));
            seq_fold_left_append(numbers@.take(index as int), seq![numbers[index as int]], 0, |acc: int, x| acc + x);
            assert(sum(numbers@.take((index + 1) as int)) == sum(numbers@.take(index as int)) + numbers[index as int] as int);
        }
        assert(sum_value as int + numbers[index as int] as int <= u64::MAX);
        assert(sum_value + numbers[index as int] as u64 <= u64::MAX);
        sum_value += numbers[index] as u64;
        
        proof {
            assert(sum_value == sum(numbers@.take((index + 1) as int)));
        }
        
        prod_value =
        match prod_value {
            Some(v) => {
                match v.checked_mul(numbers[index]) {
                    Some(new_v) => {
                        proof {
                            assert_seqs_equal!(numbers@.take((index + 1) as int) == numbers@.take(index as int).push(numbers[index as int]));
                            seq_fold_left_append(numbers@.take(index as int), seq![numbers[index as int]], 1, |acc: int, x| acc * x);
                            assert(product(numbers@.take((index + 1) as int)) == product(numbers@.take(index as int)) * numbers[index as int] as int);
                            assert(new_v == product(numbers@.take((index + 1) as int)));
                        }
                        Some(new_v)
                    },
                    None => {
                        proof {
                            assert(product(numbers@.take(index as int)) * numbers[index as int] as int > u32::MAX);
                        }
                        None
                    }
                }
            },
            None => None,
        };
    }
    assert(numbers@.take(numbers.len() as int) =~= numbers@);
    (sum_value, prod_value)
}

} // verus!

fn main() {}