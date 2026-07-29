use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
	requires
		N > 0,
		old(a).len() == N,
		old(b).len() == N,
		old(sum).len() == 1,
		N < 1000,
	ensures
		sum[0] <= 2 * N,
{
	sum.set(0, 0);
	let mut i: usize = 0;
	while (i < N as usize)
		invariant
			N > 0,
			a.len() == N,
			b.len() == N,
			sum.len() == 1,
			N < 1000,
			i <= N as usize,
			forall|j: int| 0 <= j < i ==> a[j] == 1,
		decreases N as usize - i,
	{
		a.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
		invariant
			N > 0,
			a.len() == N,
			b.len() == N,
			sum.len() == 1,
			N < 1000,
			i <= N as usize,
			sum[0] <= i as i32,
			sum[0] >= 0,
			forall|j: int| 0 <= j < N ==> a[j] == 1,
			sum[0] == i as i32,
		decreases N as usize - i,
	{
		assert(sum[0] + a[i as int] <= i as i32 + 1);
		sum.set(0, sum[0] + a[i]);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
		invariant
			N > 0,
			a.len() == N,
			b.len() == N,
			sum.len() == 1,
			N < 1000,
			i <= N as usize,
			sum[0] <= N + i as i32,
			forall|j: int| 0 <= j < i ==> b[j] == 1,
			sum[0] == N,
		decreases N as usize - i,
	{
		b.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
		invariant
			N > 0,
			a.len() == N,
			b.len() == N,
			sum.len() == 1,
			N < 1000,
			i <= N as usize,
			sum[0] <= N + i as i32,
			sum[0] >= 0,
			forall|j: int| 0 <= j < N ==> b[j] == 1,
			sum[0] == N + i as i32,
		decreases N as usize - i,
	{
		assert(sum[0] + b[i as int] <= N + i as i32 + 1);
		sum.set(0, sum[0] + b[i]);
		i = i + 1;
	}
}
}