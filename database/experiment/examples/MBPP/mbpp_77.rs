use vstd::prelude::*;

verus! {

fn replace_last_element(first: &Vec<i32>, second: &Vec<i32>) -> (replaced_list: Vec<i32>)
    requires
        first.len() > 0,
    ensures
        replaced_list@ == first@.subrange(0, first.len() - 1).add(second@),
{
    let mut replaced_list = Vec::new();
    let first_end = first.len() - 1;
    let mut index = 0;

    while index < first_end
        invariant
            first.len() > 0,
            first_end == first.len() - 1,
            index <= first_end,
            replaced_list@ == first@.subrange(0, index as int),
        decreases first_end - index,
    {
        replaced_list.push(first[index]);
        index += 1;
    }
    index = 0;
    while index < second.len()
        invariant
            first.len() > 0,
            first_end == first.len() - 1,
            index <= second.len(),
            replaced_list@ == first@.subrange(0, first_end as int).add(second@.subrange(0, index as int)),
        decreases second.len() - index,
    {
        replaced_list.push(second[index]);
        index += 1;
    }
    replaced_list
}

fn main() {}

} // verus!