use vstd::prelude::*;

fn main() {}

verus! {

spec fn count_identical(s1: Seq<i32>, s2: Seq<i32>, s3: Seq<i32>) -> int
    decreases s1.len(), s2.len(), s3.len(),
{
    if s1.len() == 0 || s2.len() == 0 || s3.len() == 0 {
        0
    } else {
        count_identical(s1.drop_last(), s2.drop_last(), s3.drop_last()) + if (s1.last() == s2.last()
            && s2.last() == s3.last()) {
            1int
        } else {
            0int
        }
    }
}

proof fn count_identical_take_property(s1: Seq<i32>, s2: Seq<i32>, s3: Seq<i32>, i: int)
    requires
        0 <= i <= s1.len(),
        s1.len() == s2.len(),
        s2.len() == s3.len(),
    ensures
        count_identical(s1.take(i), s2.take(i), s3.take(i)) == 
        if i == 0 {
            0
        } else {
            count_identical(s1.take(i - 1), s2.take(i - 1), s3.take(i - 1)) + 
            if s1[i - 1] == s2[i - 1] && s2[i - 1] == s3[i - 1] {
                1int
            } else {
                0int
            }
        }
    decreases i,
{
    if i == 0 {
        assert(s1.take(0) =~= Seq::<i32>::empty());
        assert(s2.take(0) =~= Seq::<i32>::empty());
        assert(s3.take(0) =~= Seq::<i32>::empty());
    } else {
        let s1_take = s1.take(i);
        let s2_take = s2.take(i);
        let s3_take = s3.take(i);
        
        assert(s1_take.len() == i);
        assert(s2_take.len() == i);
        assert(s3_take.len() == i);
        
        assert(s1_take.drop_last() =~= s1.take(i - 1));
        assert(s2_take.drop_last() =~= s2.take(i - 1));
        assert(s3_take.drop_last() =~= s3.take(i - 1));
        
        assert(s1_take.last() == s1[i - 1]);
        assert(s2_take.last() == s2[i - 1]);
        assert(s3_take.last() == s3[i - 1]);
        
        count_identical_take_property(s1, s2, s3, i - 1);
    }
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
        let old_count = count;
        if arr1[index] == arr2[index] && arr2[index] == arr3[index] {
            count += 1;
        }
        index += 1;
        
        // Prove that the invariant is maintained
        assert(count == count_identical(arr1@.take(index as int), arr2@.take(index as int), arr3@.take(index as int))) by {
            count_identical_take_property(arr1@, arr2@, arr3@, index as int);
            assert(count == old_count + if arr1[(index - 1) as int] == arr2[(index - 1) as int] && arr2[(index - 1) as int] == arr3[(index - 1) as int] { 1int } else { 0int });
        }
    }
    
    // Prove that the postcondition holds
    assert(count_identical(arr1@, arr2@, arr3@) == count) by {
        assert(arr1@.take(arr1.len() as int) == arr1@);
        assert(arr2@.take(arr2.len() as int) == arr2@);
        assert(arr3@.take(arr3.len() as int) == arr3@);
    }
    
    count
}

} // verus!