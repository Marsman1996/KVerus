use vstd::prelude::*;

verus! {

fn find_even_numbers(arr: &Vec<u32>) -> (even_numbers: Vec<u32>)
    ensures
        even_numbers@ == arr@.filter(|x: u32| x % 2 == 0),
{
    let mut even_numbers: Vec<u32> = Vec::new();
    let input_len = arr.len();

    let mut index = 0;
    while index < arr.len()
        invariant
            index <= arr.len(),
            even_numbers@ == arr@.subrange(0, index as int).filter(|x: u32| x % 2 == 0),
        decreases arr.len() - index,
    {
        if (arr[index] % 2 == 0) {
            even_numbers.push(arr[index]);
            assert(arr@.subrange(0, index as int).push(arr@[index as int]) =~= arr@.subrange(0, (index + 1) as int)) by {
                assert(arr@.subrange(0, index as int) + arr@.subrange(index as int, (index + 1) as int) =~= arr@.subrange(0, (index + 1) as int)) by {
                    arr@.lemma_split_at(index as int);
                }
                assert(arr@.subrange(index as int, (index + 1) as int) =~= seq![arr@[index as int]]);
            }
            reveal(Seq::filter);
            assert(arr@.subrange(0, (index + 1) as int).filter(|x: u32| x % 2 == 0) =~= arr@.subrange(0, index as int).filter(|x: u32| x % 2 == 0).push(arr@[index as int]));
            assert(even_numbers@ == arr@.subrange(0, (index + 1) as int).filter(|x: u32| x % 2 == 0));
        } else {
            assert(arr@.subrange(0, index as int).push(arr@[index as int]) =~= arr@.subrange(0, (index + 1) as int)) by {
                assert(arr@.subrange(0, index as int) + arr@.subrange(index as int, (index + 1) as int) =~= arr@.subrange(0, (index + 1) as int)) by {
                    arr@.lemma_split_at(index as int);
                }
                assert(arr@.subrange(index as int, (index + 1) as int) =~= seq![arr@[index as int]]);
            }
            reveal(Seq::filter);
            assert(arr@.subrange(0, (index + 1) as int).filter(|x: u32| x % 2 == 0) =~= arr@.subrange(0, index as int).filter(|x: u32| x % 2 == 0));
            assert(even_numbers@ == arr@.subrange(0, (index + 1) as int).filter(|x: u32| x % 2 == 0));
        }
        index += 1;
    }
    assert(arr@.subrange(0, index as int) =~= arr@);
    even_numbers
}

fn main() {}

} // verus!