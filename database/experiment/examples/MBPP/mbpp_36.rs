use vstd::prelude::*;

verus! {

fn find_negative_numbers(arr: &Vec<i32>) -> (negative_list: Vec<i32>)
    ensures
        negative_list@ == arr@.filter(|x: i32| x < 0),
{
    let mut negative_list: Vec<i32> = Vec::new();
    let input_len = arr.len();

    let mut index = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            negative_list@ == arr@.subrange(0, index as int).filter(|x: i32| x < 0),
        decreases arr.len() - index,
    {
        let old_index = index;
        proof {
            reveal(Seq::filter);
        }
        if (arr[index] < 0) {
            negative_list.push(arr[index]);
        }
        index += 1;
        proof {
            reveal(Seq::filter);
            assert(arr@.subrange(0, old_index as int).push(arr@[old_index as int]) =~= arr@.subrange(0, index as int)) by {
                arr@.lemma_split_at(index as int);
                assert(arr@.subrange(0, index as int) =~= arr@.subrange(0, old_index as int) + arr@.subrange(old_index as int, index as int));
                assert(arr@.subrange(old_index as int, index as int) =~= seq![arr@[old_index as int]]);
            }
            if arr@[old_index as int] < 0 {
                assert(negative_list@ == arr@.subrange(0, old_index as int).filter(|x: i32| x < 0).push(arr@[old_index as int]));
                assert(arr@.subrange(0, index as int).filter(|x: i32| x < 0) == arr@.subrange(0, old_index as int).filter(|x: i32| x < 0).push(arr@[old_index as int])) by {
                    let s1 = arr@.subrange(0, old_index as int);
                    let elem = arr@[old_index as int];
                    let s2 = s1.push(elem);
                    assert(s2 =~= arr@.subrange(0, index as int));
                    assert(elem < 0);
                    assert forall|i: int| 0 <= i < s1.len() implies s2[i] == s1[i] by {}
                    assert(s2[s1.len()] == elem);
                    assert(s2.filter(|x: i32| x < 0) =~= s1.filter(|x: i32| x < 0).push(elem));
                }
            } else {
                assert(negative_list@ == arr@.subrange(0, old_index as int).filter(|x: i32| x < 0));
                assert(arr@.subrange(0, index as int).filter(|x: i32| x < 0) == arr@.subrange(0, old_index as int).filter(|x: i32| x < 0)) by {
                    let s1 = arr@.subrange(0, old_index as int);
                    let elem = arr@[old_index as int];
                    let s2 = s1.push(elem);
                    assert(s2 =~= arr@.subrange(0, index as int));
                    assert(!(elem < 0));
                    assert forall|i: int| 0 <= i < s1.len() implies s2[i] == s1[i] by {}
                    assert(s2[s1.len()] == elem);
                    assert(s2.filter(|x: i32| x < 0) =~= s1.filter(|x: i32| x < 0));
                }
            }
        }
    }
    proof {
        assert(index == arr.len());
        assert(arr@.subrange(0, arr.len() as int) =~= arr@);
    }
    negative_list
}

fn main() {}

} // verus!