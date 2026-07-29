use vstd::prelude::*;
fn main() {}

verus! {

fn reverse_to_k(list: &Vec<i32>, n: usize) -> (reversed_list: Vec<i32>)
    requires
        list@.len() > 0,
        0 < n < list@.len(),
    ensures
        reversed_list@ == list@.subrange(0, n as int).reverse().add(
            list@.subrange(n as int, list.len() as int),
        ),
{
    let mut reversed_list = Vec::new();
    let mut index = 0;
    while index < n
        invariant
            list@.len() > 0,
            0 < n < list@.len(),
            index <= n,
            reversed_list@ == list@.subrange(0, n as int).subrange(n - index as int, n as int).reverse(),
        decreases n - index,
    {
        reversed_list.push(list[n - 1 - index]);
        index += 1;
    }
    index = n;
    while index < list.len()
        invariant
            list@.len() > 0,
            0 < n < list@.len(),
            n <= index <= list.len(),
            reversed_list@ == list@.subrange(0, n as int).reverse().add(
                list@.subrange(n as int, index as int)
            ),
        decreases list.len() - index,
    {
        reversed_list.push(list[index]);
        index += 1;
    }
    reversed_list
}

} // verus!