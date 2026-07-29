use vstd::prelude::*;

verus! {

fn get_positive(input: Vec<i32>) -> (positive_list: Vec<i32>)
    ensures
        positive_list@ == input@.filter(|x: i32| x > 0),
{
    let mut positive_list = Vec::<i32>::new();
    let input_len = input.len();
    
    for pos in 0..input_len
        invariant
            input_len == input.len(),
            pos <= input_len,
            positive_list@ == input@.subrange(0, pos as int).filter(|x: i32| x > 0),
    {
        let n = input[pos];
        if n > 0 {
            positive_list.push(n);
        }
        
        assert(input@.subrange(0, pos + 1) == input@.subrange(0, pos as int).push(input[pos as int])) by {
            assert(input@.subrange(0, pos as int).push(input[pos as int]) =~= input@.subrange(0, pos + 1));
        }
        
        // Prove that the filter property is preserved
        assert(positive_list@ == input@.subrange(0, (pos + 1) as int).filter(|x: i32| x > 0)) by {
            reveal(Seq::filter);
            let old_subrange = input@.subrange(0, pos as int);
            let new_subrange = input@.subrange(0, (pos + 1) as int);
            assert(new_subrange == old_subrange.push(input[pos as int]));
            
            if n > 0 {
                assert(positive_list@ == old_subrange.filter(|x: i32| x > 0).push(n));
                assert(old_subrange.push(input[pos as int]).filter(|x: i32| x > 0) =~= old_subrange.filter(|x: i32| x > 0).push(input[pos as int])) by {
                    assert(input[pos as int] > 0);
                    let filtered_old = old_subrange.filter(|x: i32| x > 0);
                    let filtered_new = old_subrange.push(input[pos as int]).filter(|x: i32| x > 0);
                    assert forall|i: int| 0 <= i < old_subrange.len() implies filtered_new[i] == #[trigger] filtered_old[i] by {}
                    assert(filtered_new.drop_last() =~= filtered_old);
                }
                assert(new_subrange.filter(|x: i32| x > 0) =~= old_subrange.filter(|x: i32| x > 0).push(n));
            } else {
                assert(positive_list@ == old_subrange.filter(|x: i32| x > 0));
                assert(old_subrange.push(input[pos as int]).filter(|x: i32| x > 0) =~= old_subrange.filter(|x: i32| x > 0)) by {
                    assert(input[pos as int] <= 0);
                    let filtered_old = old_subrange.filter(|x: i32| x > 0);
                    let filtered_new = old_subrange.push(input[pos as int]).filter(|x: i32| x > 0);
                    assert forall|i: int| 0 <= i < filtered_old.len() implies filtered_new[i] == #[trigger] filtered_old[i] by {}
                }
                assert(new_subrange.filter(|x: i32| x > 0) =~= old_subrange.filter(|x: i32| x > 0));
            }
        }
    }
    
    assert(input@.subrange(0, input_len as int) =~= input@);
    
    positive_list
}

} // verus!

fn main() {}