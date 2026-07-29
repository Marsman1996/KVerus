use vstd::prelude::*;

verus! {

fn all_sequence_equal_length(seq: &Vec<Vec<i32>>) -> (result: bool)
    requires
        seq.len() > 0,
    ensures
        result == (forall|i: int, j: int|
            (0 <= i < seq.len() && 0 <= j < seq.len()) ==> (#[trigger] seq[i].len()
                == #[trigger] seq[j].len())),
{
    let mut index = 1;
    while index < seq.len()
        invariant
            seq.len() > 0,
            1 <= index <= seq.len(),
            forall|j: int| (0 <= j < index) ==> (#[trigger] seq[j].len() == #[trigger] seq[0].len()),
        decreases seq.len() - index,
    {
        if ((&seq[index]).len() != (&seq[0]).len()) {
            return false;
        }
        index += 1;
    }
    true
}

fn main() {}

} // verus!