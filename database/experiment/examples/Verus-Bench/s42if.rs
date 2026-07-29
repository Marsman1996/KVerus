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
		sum[0] == 5 * N,
{
	sum.set(0, 0);
	let mut i: usize = 0;
	while (i < N)
		invariant
			N > 0,
			a.len() == N,
			sum.len() == 1,
			N < 1000,
			i <= N,
			forall|j: int| 0 <= j < i ==> a[j] == 1,
		decreases N - i,
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
			N < 1000,
			i <= N,
			forall|j: int| i <= j < N ==> a[j] == 1,
			forall|j: int| 0 <= j < i ==> a[j] == 5,
		decreases N - i,
	{
		if (a[i] == 1) {
			a.set(i, a[i] + 4);
		} else {
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
			N < 1000,
			i <= N,
			forall|j: int| 0 <= j < N ==> a[j] == 5,
			sum[0] == 5 * i,
		decreases N - i,
	{
		if (a[i] == 5)
		{
			sum.set(0, sum[0] + a[i]);
		} else {
			sum.set(0, sum[0] * a[i]);
		}
		i = i + 1;
	}
}
}