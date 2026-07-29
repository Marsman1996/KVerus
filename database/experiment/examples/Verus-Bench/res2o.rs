use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, b: &mut Vec<i32>, c: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
	requires
		N > 0,
		old(a).len() == N,
		old(b).len() == N,
		old(c).len() == N,
		old(sum).len() == 1,
		N < 1000,
	ensures
		sum[0] <= 3 * N,
{
	let mut i: usize = 0;
	sum.set(0, 0);

	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N,
		i <= N as usize,
		forall|j: int| 0 <= j < i as int ==> a[j] == 1,
		N < 1000,
	decreases
		N as usize - i
	{
		a.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		b.len() == N,
		i <= N as usize,
		forall|j: int| 0 <= j < i as int ==> b[j] == 1,
		N < 1000,
	decreases
		N as usize - i
	{
		b.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		c.len() == N,
		i <= N as usize,
		forall|j: int| 0 <= j < i as int ==> c[j] == 1,
		N < 1000,
	decreases
		N as usize - i
	{
		c.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N,
		sum.len() == 1,
		i <= N as usize,
		forall|j: int| 0 <= j < a.len() as int ==> a[j] == 1,
		sum[0] == i as i32,
		N < 1000,
	decreases
		N as usize - i
	{
		sum.set(0, sum[0] + a[i]);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		b.len() == N,
		sum.len() == 1,
		i <= N as usize,
		forall|j: int| 0 <= j < b.len() as int ==> b[j] == 1,
		sum[0] == N + i as i32,
		N + i as i32 <= 2 * N,
		N < 1000,
	decreases
		N as usize - i
	{
		assert(b[i as int] == 1);
		assert(sum[0] + b[i as int] == N + i as i32 + 1);
		assert(N + i as i32 + 1 <= 2 * N + 1);
		assert(N < 1000); // Use the precondition
		assert(2 * N + 1 <= 2 * 999 + 1);
		assert(2 * 999 + 1 <= i32::MAX);
		assert(2 * N + 1 <= i32::MAX);
		sum.set(0, sum[0] + b[i]);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		c.len() == N,
		sum.len() == 1,
		i <= N as usize,
		forall|j: int| 0 <= j < c.len() as int ==> c[j] == 1,
		sum[0] == 2 * N + i as i32,
		2 * N + i as i32 <= 3 * N,
		N < 1000,
	decreases
		N as usize - i
	{
		assert(c[i as int] == 1);
		assert(sum[0] + c[i as int] == 2 * N + i as i32 + 1);
		assert(2 * N + i as i32 + 1 <= 3 * N + 1);
		assert(N < 1000); // Use the precondition
		assert(3 * N + 1 <= 3 * 999 + 1);
		assert(3 * 999 + 1 <= i32::MAX);
		assert(3 * N + 1 <= i32::MAX);
		sum.set(0, sum[0] + c[i]);
		i = i + 1;
	}
}
}