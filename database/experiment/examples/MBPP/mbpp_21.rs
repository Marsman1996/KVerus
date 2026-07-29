use vstd::prelude::*;

verus! {

pub open spec fn count_frequency_rcr(seq: Seq<char>, key: char) -> int
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

fn count_frequency(arr: &Vec<char>, key: char) -> (frequency: usize)
    ensures
        count_frequency_rcr(arr@, key) == frequency,
{
    let mut index = 0;
    let mut counter = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            counter == count_frequency_rcr(arr@.take(index as int), key),
            counter <= index,
        decreases arr.len() - index,
    {
        if (arr[index] == key) {
            counter += 1;
        }
        index += 1;
        proof {
            assert(arr@.take((index - 1) as int).push(arr@[(index - 1) as int]) =~= arr@.take(index as int)) by {
                arr@.lemma_take_succ_push((index - 1) as int);
            }
            if arr@[(index - 1) as int] == key {
                assert(count_frequency_rcr(arr@.take(index as int), key) == count_frequency_rcr(arr@.take(index as int).drop_last(), key) + 1);
                assert(arr@.take(index as int).drop_last() =~= arr@.take((index - 1) as int));
                assert(count_frequency_rcr(arr@.take(index as int), key) == count_frequency_rcr(arr@.take((index - 1) as int), key) + 1);
            } else {
                assert(count_frequency_rcr(arr@.take(index as int), key) == count_frequency_rcr(arr@.take(index as int).drop_last(), key));
                assert(arr@.take(index as int).drop_last() =~= arr@.take((index - 1) as int));
                assert(count_frequency_rcr(arr@.take(index as int), key) == count_frequency_rcr(arr@.take((index - 1) as int), key));
            }
        }
    }
    proof {
        assert(arr@.take(index as int) =~= arr@);
    }
    counter
}

fn first_repeated_char(str1: &Vec<char>) -> (repeated_char: Option<(usize, char)>)
    ensures
        if let Some((idx, rp_char)) = repeated_char {
            &&& str1@.take(idx as int) =~= str1@.take(idx as int).filter(
                |x: char| count_frequency_rcr(str1@, x) <= 1,
            )
            &&& count_frequency_rcr(str1@, rp_char) > 1
        } else {
            forall|k: int|
                0 <= k < str1.len() ==> count_frequency_rcr(str1@, #[trigger] str1[k]) <= 1
        },
{
    let input_len = str1.len();
    let mut index = 0;
    while index < str1.len()
        invariant
            index <= str1.len(),
            forall|k: int| 0 <= k < index ==> count_frequency_rcr(str1@, #[trigger] str1[k]) <= 1,
            str1@.take(index as int) =~= str1@.take(index as int).filter(
                |x: char| count_frequency_rcr(str1@, x) <= 1,
            ),
        decreases str1.len() - index,
    {
        if count_frequency(&str1, str1[index]) > 1 {
            reveal(Seq::filter);
            return Some((index, str1[index]));
        }
        proof {
            reveal(Seq::filter);
            assert(str1@.take((index + 1) as int) =~= str1@.take(index as int).push(str1@[index as int])) by {
                str1@.lemma_take_succ_push(index as int);
            }
            assert(count_frequency_rcr(str1@, str1[index as int]) <= 1);
            assert forall|k: int| 0 <= k < index + 1 implies count_frequency_rcr(str1@, #[trigger] str1[k]) <= 1 by {
                if k < index {
                    assert(count_frequency_rcr(str1@, str1[k]) <= 1);
                } else {
                    assert(k == index);
                    assert(count_frequency_rcr(str1@, str1[index as int]) <= 1);
                }
            }
            assert forall|x: char| str1@.take(index as int).contains(x) && count_frequency_rcr(str1@, x) <= 1 implies str1@.take((index + 1) as int).contains(x) by {}
            assert forall|x: char| str1@.take((index + 1) as int).contains(x) && count_frequency_rcr(str1@, x) <= 1 implies str1@.take(index as int).contains(x) || x == str1@[index as int] by {}
            let filtered_take_index_plus_1 = str1@.take((index + 1) as int).filter(|y: char| count_frequency_rcr(str1@, y) <= 1);
            let filtered_take_index_push = str1@.take(index as int).filter(|y: char| count_frequency_rcr(str1@, y) <= 1).push(str1@[index as int]);
            assert forall|i: int| 0 <= i < filtered_take_index_plus_1.len() implies #[trigger] filtered_take_index_push.contains(filtered_take_index_plus_1[i]) by {}
            assert forall|i: int| 0 <= i < filtered_take_index_push.len() implies #[trigger] filtered_take_index_plus_1.contains(filtered_take_index_push[i]) by {}
            assert(filtered_take_index_plus_1.len() == filtered_take_index_push.len());
            assert forall|i: int| 0 <= i < filtered_take_index_plus_1.len() implies filtered_take_index_plus_1[i] == filtered_take_index_push[i] by {}
            assert(str1@.take((index + 1) as int).filter(|x: char| count_frequency_rcr(str1@, x) <= 1) =~= str1@.take(index as int).filter(|x: char| count_frequency_rcr(str1@, x) <= 1).push(str1@[index as int]));
            assert(str1@.take((index + 1) as int) =~= str1@.take((index + 1) as int).filter(|x: char| count_frequency_rcr(str1@, x) <= 1));
        }
        index += 1;
    }
    None
}

fn main() {}

} // verus!