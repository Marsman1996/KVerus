use vstd::prelude::*;

verus! {

fn contains(arr: &Vec<i32>, key: i32) -> (result: bool)
    ensures
        result == (exists|i: int| 0 <= i < arr.len() && (arr[i] == key)),
{
    let mut i = 0;
    while i < arr.len()
        invariant
            forall|m: int| 0 <= m < i ==> (arr[m] != key),
    {
        if (arr[i] == key) {
            return true;
        }
        i += 1;
    }
    false
}

fn intersection(arr1: &Vec<i32>, arr2: &Vec<i32>) -> (result: Vec<i32>)
    ensures
        forall|i: int|
            0 <= i < result.len() ==> (arr1@.contains(#[trigger] result[i]) && arr2@.contains(
                #[trigger] result[i],
            )),
        forall|i: int, j: int| 0 <= i < j < result.len() ==> result[i] != result[j],
{
    let mut output_arr = Vec::new();
    let ghost mut out_arr_len: int = 0;

    let mut index = 0;
    while index < arr1.len()
        invariant
            forall|i: int|
                0 <= i < output_arr.len() ==> (arr1@.contains(#[trigger] output_arr[i])
                    && arr2@.contains(#[trigger] output_arr[i])),
            forall|m: int, n: int| 0 <= m < n < output_arr.len() ==> output_arr[m] != output_arr[n],
    {
        if (contains(arr2, arr1[index]) && !contains(&output_arr, arr1[index])) {
            output_arr.push(arr1[index]);
            proof {
                out_arr_len = out_arr_len + 1;
            }
        }
        index += 1;
    }
    output_arr
}

fn main() {}

} // verus!
