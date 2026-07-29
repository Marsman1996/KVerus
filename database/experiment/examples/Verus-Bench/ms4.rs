use vstd::prelude::*;
fn main() {}
verus!{

pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32) 
	requires 
		old(a).len() == N,
		old(sum).len() == 1,
		N > 0,
		N < 1000,
	ensures
		sum[0] <= 3 * N,
{
	let mut i: usize = 0;
	while (i < N as usize)
		invariant
			a.len() == N,
			sum.len() == 1,
			N > 0,
			N < 1000,
			i <= N as usize,
			forall|j: int| 0 <= j < i ==> a[j as int] == (j % 4) as i32,
		decreases N as usize - i,
	{
		a.set(i, (i % 4) as i32);
		i = i + 1;
	}

	i = 0;
	sum.set(0, 0);
	
	while (i < N as usize)
		invariant
			a.len() == N,
			sum.len() == 1,
			N > 0,
			N < 1000,
			i <= N as usize,
			forall|j: int| 0 <= j < N ==> a[j as int] == (j % 4) as i32,
			forall|j: int| 0 <= j < N ==> 0 <= #[trigger] a[j as int] <= 3,
			sum[0] <= 3 * i as i32,
		decreases N as usize - i,
	{
		if (i == 0) {
			sum.set(0, 0);
		} else {
			assert(a[i as int] >= 0 && a[i as int] <= 3);
			assert(sum[0] <= 3 * i as i32);
			assert(sum[0] + a[i as int] <= 3 * i as i32 + 3);
			assert(sum[0] + a[i as int] <= 3 * (i as i32 + 1));
			sum.set(0, sum[0] + a[i]);
		}
		i = i + 1;
	}
}
}