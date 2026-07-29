use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: usize)
	requires
		N > 0,
		old(a).len() == N,
		old(sum).len() == 1,
		N < 1000,
	ensures
		sum[0] == 6 * N,
{
	let mut i: usize = 0;
	sum.set(0, 0);

	while (i < N)
		invariant
			i <= N,
			a@.len() == N,
			sum@.len() == 1,
			forall|j: int| 0 <= j < i as int ==> a@[j] == 1,
		decreases (N - i)
	{
		a.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N)
		invariant
			i <= N,
			a@.len() == N,
			sum@.len() == 1,
			forall|j: int| 0 <= j < i as int && j < N as int ==> a@[j] == 6,
			forall|j: int| i as int <= j < N as int ==> a@[j] == 1,
		decreases (N - i)
	{
		if (a[i] == 1) {
			a.set(i, a[i] + 5);
		} else {
			// This branch is actually unreachable since all elements are 1 after the first loop
			assert(a@[i as int] == 6);
		}
		i = i + 1;
	}

	i = 0;
	while (i < N)
		invariant
			i <= N,
			a@.len() == N,
			sum@.len() == 1,
			forall|j: int| 0 <= j < N as int ==> a@[j] == 6,
			sum@[0] == 6 * i as int,
			sum@[0] + 6 * (N as int - i as int) == 6 * N as int,
			N < 1000, // Added to prevent overflow
		decreases (N - i)
	{
		if (a[i] == 6)
		{
			assert(sum@[0] + a@[i as int] == sum@[0] + 6);
			assert(sum@[0] + 6 <= 6 * N as int);
			sum.set(0, sum[0] + a[i]);
			assert(sum@[0] == 6 * (i as int + 1)); // Added to maintain loop invariant
		} else {
			// This branch is unreachable since all elements are 6 after the second loop
			assert(false);
		}
		i = i + 1;
	}
}
}