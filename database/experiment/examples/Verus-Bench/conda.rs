use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
	requires
		N > 0,
		old(a).len() == N,
		old(sum).len() == 1,
		N < 1000,
	ensures
		sum[0] == 2 * N,
{
	sum.set(0, 0);
	let mut i: usize = 0;
	while (i < N as usize)
		invariant
			N > 0,
			a@.len() == N as usize,
			sum@.len() == 1,
			i <= N as usize,
			forall|j: int| 0 <= j && j < i as int ==> a@[j] == 1,
		decreases (N as usize - i)
	{
		a.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
		invariant
			N > 0,
			a@.len() == N as usize,
			sum@.len() == 1,
			i <= N as usize,
			forall|j: int| 0 <= j && j < i as int ==> a@[j] == 2,
			forall|j: int| j >= i as int && j < N as int ==> a@[j] == 1,
		decreases (N as usize - i)
	{
		if (a[i] == 1) {
			a.set(i, a[i] + 1);
		} else {
			a.set(i, a[i] - 1);
		}
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
		invariant
			N > 0,
			a@.len() == N as usize,
			sum@.len() == 1,
			i <= N as usize,
			sum@[0] == i as i32 * 2,
			forall|j: int| 0 <= j && j < N as int ==> a@[j] == 2,
			N < 1000, // Added to prevent overflow
		decreases (N as usize - i)
	{
		assert(a@[i as int] == 2); // Explicitly assert that a[i] is 2
		assert(sum@[0] + a@[i as int] <= 2 * N); // Prove no overflow can occur
		sum.set(0, sum[0] + a[i]);
		i = i + 1;
	}
}
}