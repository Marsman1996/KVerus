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
		sum[0] <= 4 * N,
{
	let mut i: usize = 0;
	while (i < N as usize)
		invariant
			a.len() == N,
			sum.len() == 1,
			N > 0,
			N < 1000,
			i <= N as usize,
			forall|j: int| 0 <= j < i ==> a@[j] == (if j % 4 == 0 { 4int } else { 0int }),
		decreases N as usize - i,
	{
		if (i % 4 == 0) {
			a.set(i, 4);
		} else {
			a.set(i, 0);
		}
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
			forall|j: int| 0 <= j < N ==> a@[j] == (if j % 4 == 0 { 4int } else { 0int }),
			sum[0] <= 4 * i as i32,
			sum[0] >= 0,
		decreases N as usize - i,
	{
		sum.set(0, sum[0] + a[i]);
		i = i + 1;
	}
}
}