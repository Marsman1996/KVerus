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
		sum[0] == 2 * N,
{
	sum.set(0, 0);
	let mut i: usize = 0;
	while (i < N)
	invariant
		i <= N,
		a.len() == N,
		sum.len() == 1,
		forall|j: usize| j < i && j < N ==> a@[j as int] == 1,
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
		a.len() == N,
		sum.len() == 1,
		forall|j: usize| j < i && j < N ==> a@[j as int] == 2,
		forall|j: usize| i <= j && j < N ==> a@[j as int] == 1,
	decreases
		N - i,
	{
		if (a[i] == 1) {
			a.set(i, a[i] + 1);
		} else {
			// This branch is unreachable because a[i] == 1 for all i < N
			assert(a@[i as int] == 1);
			a.set(i, a[i]);
		}
		i = i + 1;
	}

	i = 0;
	while (i < N)
	invariant
		i <= N,
		a.len() == N,
		sum.len() == 1,
		forall|j: usize| j < N ==> a@[j as int] == 2,
		sum[0] == 2 * i,
		N < 1000,
	decreases
		N - i,
	{
		if (a[i] == 2) {
			assert(sum[0] + a@[i as int] == 2 * i + 2);
			assert(2 * i + 2 == 2 * (i + 1));
			sum.set(0, sum[0] + a[i]);
		} else {
			// This branch is unreachable because a[i] == 2 for all i < N
			assert(a@[i as int] == 2);
			sum.set(0, sum[0]);
		}
		i = i + 1;
	}
}
}