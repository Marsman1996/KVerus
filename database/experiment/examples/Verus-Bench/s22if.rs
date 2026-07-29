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
		sum[0] == 3 * N,
{
	sum.set(0, 0);
	let mut i: usize = 0;
	while (i < N)
	invariant
		i <= N,
		a@.len() == N,
		sum@.len() == 1,
		forall|j: int| 0 <= j < i as int ==> a@[j] == 1,
		forall|j: int| i as int <= j < N as int ==> a@[j] == old(a)@[j],
	decreases
		N - i,
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
		forall|j: int| 0 <= j < i as int && j < N as int ==> a@[j] == 3,
		forall|j: int| i as int <= j < N as int ==> a@[j] == 1,
	decreases
		N - i,
	{
		if (a[i] == 1) {
			a.set(i, a[i] + 2);
		} else {
			assert(a@[i as int] == 3);
			a.set(i, a[i] - 0);
		}
		i = i + 1;
	}

	i = 0;
	while (i < N)
	invariant
		i <= N,
		a@.len() == N,
		sum@.len() == 1,
		forall|j: int| 0 <= j < N as int ==> a@[j] == 3,
		sum@[0] == 3 * i as int,
		sum@[0] + 3 <= i32::MAX as int,
		N < 1000,
	decreases
		N - i,
	{
		if (a[i] == 3) {
			sum.set(0, sum[0] + a[i]);
			assert(sum@[0] == 3 * i as int + 3);
			assert(sum@[0] == 3 * (i + 1) as int);
		} else {
			assert(false);
		}
		i = i + 1;
	}
}
}