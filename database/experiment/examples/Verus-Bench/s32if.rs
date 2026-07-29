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
		sum[0] == 4 * N,
{
	sum.set(0, 0);
	let mut i: usize = 0;
	while (i < N)
	invariant
		N > 0,
		a.len() == N,
		sum.len() == 1,
		i <= N,
		forall|j: int| 0 <= j < i as int ==> a@[j] == 1,
	decreases
		N - i,
	{
		a.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N)
	invariant
		N > 0,
		a.len() == N,
		sum.len() == 1,
		i <= N,
		forall|j: int| 0 <= j < i as int ==> a@[j] == 4,
		forall|j: int| i as int <= j < N as int ==> a@[j] == 1,
	decreases
		N - i,
	{
		if (a[i] == 1) {
			a.set(i, a[i] + 3);
		} else {
			assert(false); // This branch is unreachable due to the invariant
			a.set(i, a[i] - 1);
		}
		i = i + 1;
	}

	i = 0;
	while (i < N)
	invariant
		N > 0,
		a.len() == N,
		sum.len() == 1,
		i <= N,
		forall|j: int| 0 <= j < N as int ==> a@[j] == 4,
		sum[0] == 4 * i as int,
		sum[0] as int + 4 <= i32::MAX as int,
		(i as int) * 4 + 4 <= i32::MAX as int,
		N < 1000, // Added from requires
	decreases
		N - i,
	{
		if (a[i] == 4) {
			sum.set(0, sum[0] + a[i]);
			assert(sum[0] == 4 * i as int + 4);
			assert(sum[0] == 4 * (i + 1) as int);
		} else {
			assert(false); // This branch is unreachable due to the invariant
			sum.set(0, sum[0] * a[i]);
		}
		i = i + 1;
	}
}
}