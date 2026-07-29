//an example from Verus tutorial. VERY difficult.

use vstd::prelude::*;
fn main() {}

verus!{
     
pub proof fn lemma_len_intersect<A>(s1: Set<A>, s2: Set<A>)
    requires
        s1.finite(),
    ensures
        s1.intersect(s2).len() <= s1.len(),
    decreases
        s1.len(),
{
    if s1 =~= Set::empty() {
        // Base case: empty set
        // The intersection with any set is empty, so the length is 0
        assert(s1.intersect(s2) =~= Set::empty());
        assert(s1.intersect(s2).len() == 0);
        assert(s1.len() == 0);
    } else {
        // Get an element from s1
        let a = choose|a: A| s1.contains(a);
        let s1_without_a = s1.difference(Set::new(|x: A| x == a));
        
        // Prove s1_without_a is finite and its size is smaller
        assert(s1.contains(a));
        assert(s1_without_a.finite());
        
        // Use Set::remove_one axiom to prove the size relationship
        assert(s1_without_a =~= s1.remove(a)); 
        assert(s1.len() == s1.remove(a).len() + 1);
        assert(s1_without_a.len() < s1.len());
        
        // Recursive call on the smaller set
        lemma_len_intersect(s1_without_a, s2);
        
        // Use axioms to reason about the intersection
        if s2.contains(a) {
            // Element a is in both s1 and s2
            assert(s1.intersect(s2).contains(a));
            assert(s1_without_a.intersect(s2).len() <= s1_without_a.len());
            
            // The size of s1 is one more than s1_without_a
            assert(s1.difference(Set::new(|x: A| x == a)).len() == s1.len() - 1);
            assert(s1.len() == s1_without_a.len() + 1);
            
            // The size of the intersection with a is one more than without a
            assert(s1.intersect(s2) =~= s1_without_a.intersect(s2).insert(a));
            assert(s1.intersect(s2).len() == s1_without_a.intersect(s2).len() + 1);
            assert(s1.intersect(s2).len() <= s1.len());
        } else {
            // Element a is not in s2
            assert(!s1.intersect(s2).contains(a));
            assert(s1.intersect(s2) =~= s1_without_a.intersect(s2));
            assert(s1_without_a.intersect(s2).len() <= s1_without_a.len());
            assert(s1.difference(Set::new(|x: A| x == a)).len() == s1.len() - 1);
            assert(s1.len() == s1_without_a.len() + 1);
            assert(s1.intersect(s2).len() <= s1.len());
        }
    }
}
}