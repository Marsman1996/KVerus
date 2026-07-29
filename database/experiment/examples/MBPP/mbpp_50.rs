use vstd::prelude::*;
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
            reversed_list@ == list@.subrange(0, index as int).reverse(),
        decreases n - index,
    {
        reversed_list.push(list[n - 1 - index]);
        assert(reversed_list@ == list@.subrange(0, index as int).reverse().push(list@[n - 1 - index]));
        assert(list@.subrange(0, (index + 1) as int) == list@.subrange(0, index as int).push(list@[index as int]));
        assert(list@.subrange(0, (index + 1) as int).reverse() == list@.subrange(0, index as int).push(list@[index as int]).reverse());
        assert(list@.subrange(0, index as int).push(list@[index as int]).reverse() == seq![list@[index as int]].add(list@.subrange(0, index as int).reverse()));
        assert(list@[index as int] == list@[n - 1 - (n - 1 - index)]) by {
            assert(index < n);
            assert(n - 1 - (n - 1 - index) == index);
        }
        assert(list@[n - 1 - index] == list@[index as int]) by {
            assert(n - 1 - (n - 1 - index) == index);
            assert(list@[index as int] == list@[n - 1 - (n - 1 - index)]);
        }
        assert(list@.subrange(0, (index + 1) as int).reverse() == seq![list@[n - 1 - index]].add(list@.subrange(0, index as int).reverse()));
        assert(reversed_list@ == list@.subrange(0, (index + 1) as int).reverse()) by {
            assert(reversed_list@ == list@.subrange(0, index as int).reverse().push(list@[n - 1 - index]));
            assert(list@.subrange(0, (index + 1) as int).reverse() == seq![list@[n - 1 - index]].add(list@.subrange(0, index as int).reverse()));
            assert(list@.subrange(0, index as int).reverse().push(list@[n - 1 - index]) == list@.subrange(0, index as int).reverse().add(seq![list@[n - 1 - index]]));
            assert(seq![list@[n - 1 - index]].add(list@.subrange(0, index as int).reverse()) == list@.subrange(0, index as int).reverse().add(seq![list@[n - 1 - index]]));
        }
        index += 1;
    }
    index = n;
    while index < list.len()
        invariant
            list@.len() > 0,
            0 < n < list@.len(),
            n <= index <= list.len(),
            reversed_list@ == list@.subrange(0, n as int).reverse().add(
                list@.subrange(n as int, index as int),
            ),
        decreases list.len() - index,
    {
        reversed_list.push(list[index]);
        index += 1;
    }
    reversed_list
}

fn main() {}

} // verus!