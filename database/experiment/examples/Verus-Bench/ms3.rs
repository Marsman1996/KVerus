use vstd::prelude::*;
fn main() {}
verus!{

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32) 
	requires 
		old(a).len() == N as usize,
		old(sum).len() == 1,
		N > 0,
		N < 1000,
	ensures
		sum[0] <= 2 * N,
{
	let mut i: usize = 0;
	while (i < N as usize)
	invariant
		a.len() == N as usize,
		i <= N as usize,
		forall|j: int| 0 <= j < i as int ==> a@[j] == (j as usize % 3) as i32,
	decreases (N as usize - i)
	{
		a.set(i, (i % 3) as i32);
		i = i + 1;
	}

	i = 0;
	sum.set(0, 0);
	
	while (i < N as usize)
	invariant
		a.len() == N as usize,
		sum.len() == 1,
		i <= N as usize,
		N > 0,
		N < 1000,
		i == 0 ==> sum[0] == 0,
		i > 0 ==> sum[0] <= 2 * i as i32,
		forall|j: int| 0 <= j < N as int ==> a@[j] <= 2,
		forall|j: int| 0 <= j < N as int ==> a@[j] >= 0,
	decreases (N as usize - i)
	{
		if (i == 0) {
			sum.set(0, 0);
		} else {
			assert(a@[i as int] <= 2);
			assert(a@[i as int] >= 0);
			assert(sum[0] <= 2 * i as i32);
			assert(sum[0] + a@[i as int] <= 2 * i as i32 + 2);
			assert(2 * i as i32 + 2 <= 2 * (i + 1) as i32);
			sum.set(0, sum[0] + a[i]);
		}
		i = i + 1;
	}

	assert(forall|j: int| 0 <= j < N as int ==> a@[j] <= 2);
}
}