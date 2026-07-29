use vstd::prelude::*;
fn main() {}

verus! {

spec fn rotation_split(len: usize, n: usize) -> int {
    len - (n % len)
}

fn rotate_right(list: &Vec<u32>, n: usize) -> (new_list: Vec<u32>)
    requires
        list.len() > 0,
    ensures
        new_list.len() == list.len(),
        new_list@ == list@.subrange(rotation_split(list.len(), n) as int, list@.len() as int).add(
            list@.subrange(0, rotation_split(list.len(), n) as int),
        ),
{
    let rotation = n % list.len();
    let split_index = list.len() - rotation;
    let mut new_list = Vec::with_capacity(list.len());
    let mut index = split_index;

    while index < list.len()
        invariant
            list.len() > 0,
            split_index <= list.len(),
            split_index <= index <= list.len(),
            new_list.len() == index - split_index,
            forall|i: int| 0 <= i < (index - split_index) ==> new_list@[i] == list@[split_index + i],
        decreases list.len() - index,
    {
        new_list.push(list[index]);
        index += 1;
    }
    index = 0;
    while index < split_index
        invariant
            list.len() > 0,
            split_index <= list.len(),
            0 <= index <= split_index,
            new_list.len() == (list.len() - split_index) + index,
            forall|i: int| 0 <= i < (list.len() - split_index) ==> new_list@[i] == list@[split_index + i],
            forall|i: int| 0 <= i < index ==> new_list@[(list.len() - split_index) + i] == list@[i],
        decreases split_index - index,
    {
        new_list.push(list[index]);
        index += 1;
    }
    
    proof {
        assert(new_list.len() == (list.len() - split_index) + split_index);
        assert(new_list.len() == list.len());
        
        assert(split_index == rotation_split(list.len(), n));
        
        let first_part = list@.subrange(split_index as int, list@.len() as int);
        let second_part = list@.subrange(0, split_index as int);
        
        assert(forall|i: int| 0 <= i < first_part.len() ==> 
            new_list@[i] == first_part[i]);
        assert(forall|i: int| 0 <= i < second_part.len() ==> 
            new_list@[first_part.len() + i] == second_part[i]);
        
        assert(new_list@ == first_part.add(second_part));
    }
    
    new_list
}

} // verus!