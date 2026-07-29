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
		sum[0] == 4 * N,
{
	sum.set(0, 0);
	let mut i: usize = 0;
	while (i < N as usize)
		invariant
			N > 0,
			a.len() == N,
			sum.len() == 1,
			N < 1000,
			i <= N,
			forall|j: int| 0 <= j < i ==> a[j] == 4,
		decreases N - i,
	{
		a.set(i, 4);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
		invariant
			N > 0,
			a.len() == N,
			sum.len() == 1,
			N < 1000,
			i <= N,
			forall|j: int| 0 <= j < a.len() ==> a[j] == 4,
			sum[0] == 4 * i,
		decreases N - i,
	{
		if (a[i] == 4) {
			sum.set(0, sum[0] + a[i]);
		} else {
			sum.set(0, sum[0] * a[i]);
		}
		i = i + 1;
	}
}
}