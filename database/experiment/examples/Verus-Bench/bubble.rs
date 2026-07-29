use vstd::prelude::*;
fn main() {}

verus! {
    spec fn sorted_between(a: Seq<u32>, from: int, to: int) -> bool {
        forall |i: int, j:int|  from <= i < j < to ==> a[i] <= a[j]
    }
 
 
    spec fn is_reorder_of<T>(r: Seq<int>, p: Seq<T>, s: Seq<T>) -> bool {
    &&& r.len() == s.len()
    &&& forall|i: int| 0 <= i < r.len() ==> 0 <= #[trigger] r[i] < r.len()
    &&& forall|i: int, j: int| 0 <= i < j < r.len() ==> r[i] != r[j]
    &&& p =~= r.map_values(|i: int| s[i])
    }
 
    fn test1(nums: &mut Vec<u32>)
        ensures
            sorted_between(nums@, 0, nums@.len() as int),
            exists|r: Seq<int>| is_reorder_of(r, nums@, old(nums)@),
    {
        let n = nums.len();
        if n == 0 {
            proof {
                let r = Seq::empty();
                assert(is_reorder_of(r, nums@, old(nums)@));
                assert(exists|r: Seq<int>| is_reorder_of(r, nums@, old(nums)@));
            }
            return;
        }
        
        // Track the permutation
        let mut r: Vec<usize> = Vec::new();
        for i in 0..n {
            r.push(i);
        }
        
        for i in 1..n
            invariant
                0 <= i <= n,
                nums.len() == n,
                r.len() == n,
                sorted_between(nums@, 0, i as int),
                forall|k: int| 0 <= k < r@.len() ==> 0 <= #[trigger] r@[k] < r@.len(),
                forall|k: int, l: int| 0 <= k < l < r@.len() ==> r@[k] != r@[l],
                nums@ =~= r@.map_values(|idx: int| old(nums)@[idx]),
        {
            let mut j = i;
            while j > 0
                invariant
                    0 <= j <= i,
                    nums.len() == n,
                    r.len() == n,
                    sorted_between(nums@, 0, j as int),
                    sorted_between(nums@, j as int, (i+1) as int),
                    forall|k: int| j as int <= k < i as int && j > 0 ==> nums@[j-1] <= #[trigger] nums@[k],
                    forall|k: int| 0 <= k < r@.len() ==> 0 <= #[trigger] r@[k] < r@.len(),
                    forall|k: int, l: int| 0 <= k < l < r@.len() ==> r@[k] != r@[l],
                    nums@ =~= r@.map_values(|idx: int| old(nums)@[idx]),
                decreases j,
            {
                if j > 0 && nums[j - 1] > nums[j] {
                    let temp = nums[j - 1];
                    let val_j = nums[j];
                    nums.set(j - 1, val_j);
                    nums.set(j, temp);
                    
                    // Update permutation
                    let r_j_1 = r[j - 1];
                    let r_j = r[j];
                    r.set(j - 1, r_j);
                    r.set(j, r_j_1);
                }
                j -= 1;
            }
        }
        
        proof {
            assert(sorted_between(nums@, 0, nums@.len() as int));
            assert(is_reorder_of(r@.map(|i: int, x: usize| x as int), nums@, old(nums)@));
            assert(exists|r: Seq<int>| is_reorder_of(r, nums@, old(nums)@));
        }
    }
}