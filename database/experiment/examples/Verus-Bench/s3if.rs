use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
	requires
		N > 0,
		old(a).len() == N as usize,
		old(sum).len() == 1,
		N < 1000,
	ensures
		sum[0] == 3 * N,
{
	let mut i: usize = 0;
	sum.set(0, 0);

	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		N < 1000,
		i <= N as usize,
		forall|j: int| 0 <= j < i as int ==> a@[j] == 3,
	decreases (N as usize - i)
	{
		a.set(i, 3);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		N < 1000,
		i <= N as usize,
		forall|j: int| 0 <= j < N as int ==> a@[j] == 3,
		sum[0] == 3 * (i as i32),
	decreases (N as usize - i)
	{
		if (a[i] == 3) {
			sum.set(0, sum[0] + a[i]);
		} else {
			// This branch is actually unreachable because all elements are 3
			assert(a@[i as int] == 3);
			sum.set(0, sum[0] + a[i]); // Changed to addition to avoid overflow
		}
		i = i + 1;
	}
}
}