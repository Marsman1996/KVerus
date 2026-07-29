use vstd::prelude::*;

fn main() {}

verus! {

pub open spec fn count_frequency_rcr(seq: Seq<u8>, key: u8) -> int
    decreases seq.len(),
{
    if seq.len() == 0 {
        0
    } else {
        count_frequency_rcr(seq.drop_last(), key) + if (seq.last() == key) {
            1 as int
        } else {
            0 as int
        }
    }
}

proof fn lemma_count_frequency_rcr_append(seq: Seq<u8>, key: u8)
    ensures
        count_frequency_rcr(seq, key) == count_frequency_rcr(seq.take(seq.len() - 1), key) + if seq.len() > 0 && seq.last() == key { 1 as int } else { 0 as int },
    decreases seq.len(),
{
    if seq.len() == 0 {
        assert(count_frequency_rcr(seq, key) == 0);
        assert(seq.take(seq.len() - 1) =~= Seq::empty());
        assert(count_frequency_rcr(seq.take(seq.len() - 1), key) == 0);
    } else {
        assert(seq.drop_last() =~= seq.take(seq.len() - 1));
        assert(count_frequency_rcr(seq, key) == count_frequency_rcr(seq.drop_last(), key) + if seq.last() == key { 1 as int } else { 0 as int });
        assert(count_frequency_rcr(seq.drop_last(), key) == count_frequency_rcr(seq.take(seq.len() - 1), key));
    }
}

proof fn lemma_count_frequency_rcr_iterative(seq: Seq<u8>, key: u8, idx: int)
    requires
        0 <= idx <= seq.len(),
    ensures
        count_frequency_rcr(seq, key) == count_frequency_rcr(seq.take(idx), key) + count_frequency_rcr(seq.skip(idx), key),
    decreases seq.len() - idx,
{
    if idx == seq.len() {
        assert(seq.take(idx) =~= seq);
        assert(seq.skip(idx) =~= Seq::empty());
        assert(count_frequency_rcr(seq.skip(idx), key) == 0);
    } else {
        lemma_count_frequency_rcr_iterative(seq, key, idx + 1);
        lemma_count_frequency_rcr_append(seq.skip(idx), key);
        assert(seq.skip(idx).take(1) =~= seq![seq[idx]]);
        assert(seq.skip(idx).skip(1) =~= seq.skip(idx + 1));
        assert(seq.take(idx + 1) =~= seq.take(idx).push(seq[idx]));
        lemma_count_frequency_rcr_append(seq.take(idx + 1), key);
        
        // Prove the main equality by expanding both sides
        assert(count_frequency_rcr(seq, key) == count_frequency_rcr(seq.take(idx + 1), key) + count_frequency_rcr(seq.skip(idx + 1), key));
        
        // Use the lemma to establish the relationship for seq.take(idx + 1)
        assert(count_frequency_rcr(seq.take(idx + 1), key) == count_frequency_rcr(seq.take(idx), key) + if seq.take(idx + 1).len() > 0 && seq.take(idx + 1).last() == key { 1 as int } else { 0 as int });
        assert(seq.take(idx + 1).last() == seq[idx]);
        
        // Use the lemma to establish the relationship for seq.skip(idx)
        assert(count_frequency_rcr(seq.skip(idx), key) == count_frequency_rcr(seq.skip(idx).take(seq.skip(idx).len() - 1), key) + if seq.skip(idx).len() > 0 && seq.skip(idx).last() == key { 1 as int } else { 0 as int });
        assert(seq.skip(idx).take(seq.skip(idx).len() - 1) =~= seq.skip(idx + 1));
        assert(seq.skip(idx).last() == seq[idx]);
        
        // Now we can prove the desired equality
        assert(count_frequency_rcr(seq.take(idx), key) + count_frequency_rcr(seq.skip(idx), key) 
               == count_frequency_rcr(seq.take(idx), key) + (count_frequency_rcr(seq.skip(idx + 1), key) + if seq[idx] == key { 1 as int } else { 0 as int }));
        assert(count_frequency_rcr(seq.take(idx), key) + count_frequency_rcr(seq.skip(idx), key) 
               == count_frequency_rcr(seq.take(idx), key) + if seq[idx] == key { 1 as int } else { 0 as int } + count_frequency_rcr(seq.skip(idx + 1), key));
        assert(count_frequency_rcr(seq.take(idx), key) + count_frequency_rcr(seq.skip(idx), key) 
               == count_frequency_rcr(seq.take(idx + 1), key) + count_frequency_rcr(seq.skip(idx + 1), key));
        assert(count_frequency_rcr(seq.take(idx), key) + count_frequency_rcr(seq.skip(idx), key) 
               == count_frequency_rcr(seq, key));
    }
}

fn count_frequency(arr: &[u8], key: u8) -> (frequency: usize)
    ensures
        count_frequency_rcr(arr@, key) == frequency,
{
    let mut index = 0;
    let mut counter = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            counter <= usize::MAX,
            count_frequency_rcr(arr@.take(index as int), key) == counter,
        decreases arr.len() - index,
    {
        proof {
            lemma_count_frequency_rcr_iterative(arr@, key, index as int);
        }
        if (arr[index] == key) {
            assert(counter < usize::MAX) by {
                lemma_count_frequency_rcr_iterative(arr@, key, index as int);
                assert(count_frequency_rcr(arr@, key) == count_frequency_rcr(arr@.take(index as int), key) + count_frequency_rcr(arr@.skip(index as int), key));
                assert(count_frequency_rcr(arr@.take(index as int), key) == counter);
                assert(count_frequency_rcr(arr@.skip(index as int), key) >= 0);
                assert(count_frequency_rcr(arr@, key) >= counter);
                assert(count_frequency_rcr(arr@, key) <= arr.len());
                assert(arr.len() <= usize::MAX);
            }
            counter += 1;
        }
        index += 1;
        proof {
            lemma_count_frequency_rcr_append(arr@.take(index as int), key);
            assert(arr@.take(index as int) =~= arr@.take((index - 1) as int).push(arr[(index - 1) as int]));
        }
    }
    proof {
        assert(arr@.take(index as int) =~= arr@);
    }
    counter
}

proof fn lemma_filter_take_property(seq: Seq<u8>, idx: int, key: u8)
    requires
        0 <= idx <= seq.len(),
        count_frequency_rcr(seq, key) > 1,
    ensures
        seq.take(idx).filter(|x: u8| count_frequency_rcr(seq, x) <= 1) =~= 
        seq.take(idx).filter(|x: u8| count_frequency_rcr(seq, x) <= 1),
{
}

fn first_repeated_char(str1: &[u8]) -> (repeated_char: Option<(usize, u8)>)
    ensures
        if let Some((idx, rp_char)) = repeated_char {
            &&& str1@.take(idx as int) =~= str1@.take(idx as int).filter(
                |x: u8| count_frequency_rcr(str1@, x) <= 1,
            )
            &&& count_frequency_rcr(str1@, rp_char) > 1
        } else {
            forall|k: int|
                0 <= k < str1.len() ==> count_frequency_rcr(str1@, #[trigger] str1[k]) <= 1
        },
{
    let mut index = 0;
    while index < str1.len()
        invariant
            index <= str1.len(),
            forall|k: int| 0 <= k < index ==> count_frequency_rcr(str1@, #[trigger] str1[k]) <= 1,
            str1@.take(index as int) =~= str1@.take(index as int).filter(
                |x: u8| count_frequency_rcr(str1@, x) <= 1,
            ),
        decreases str1.len() - index,
    {
        if count_frequency(&str1, str1[index]) > 1 {
            proof {
                assert(count_frequency_rcr(str1@, str1[index as int]) > 1);
            }
            return Some((index, str1[index]));
        }
        proof {
            assert(count_frequency_rcr(str1@, str1[index as int]) <= 1);
            assert(str1@.take((index + 1) as int) =~= str1@.take(index as int).push(str1[index as int]));
            
            // Prove that the new element satisfies the filter condition
            assert(count_frequency_rcr(str1@, str1[index as int]) <= 1);
            
            // Prove the filter property is maintained
            let new_take = str1@.take((index + 1) as int);
            let old_take = str1@.take(index as int);
            let new_elem = str1[index as int];
            
            assert(new_take =~= old_take.push(new_elem));
            assert(old_take =~= old_take.filter(|x: u8| count_frequency_rcr(str1@, x) <= 1));
            assert(count_frequency_rcr(str1@, new_elem) <= 1);
            
            // The filter of the extended sequence equals the extended sequence
            assert(new_take.filter(|x: u8| count_frequency_rcr(str1@, x) <= 1) =~= new_take) by {
                assert(forall |idx: int| #![auto] 0 <= idx < new_take.len() ==> count_frequency_rcr(str1@, new_take[idx]) <= 1) by {
                    if idx < old_take.len() {
                        assert(new_take[idx] == old_take[idx]);
                        assert(count_frequency_rcr(str1@, old_take[idx]) <= 1);
                    } else {
                        assert(idx == old_take.len());
                        assert(new_take[idx] == new_elem);
                        assert(count_frequency_rcr(str1@, new_elem) <= 1);
                    }
                }
            }
        }
        index += 1;
    }
    None
}

} // verus!