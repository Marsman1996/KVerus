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
		sum[0] <= 2 * N,
{
	let mut i: usize = 0;
	while (i < N as usize)
		invariant
			a.len() == N,
			sum.len() == 1,
			N > 0,
			N < 1000,
			i <= N as usize,
			forall|j: int| 0 <= j < i ==> a[j] == if j % 2 == 0 { 2int } else { 0int },
		decreases N as usize - i,
	{
		if (i % 2 == 0) {
			a.set(i, 2);
		} else {
			a.set(i, 0);
		}
		i = i + 1;
	}

	i = 0;
	
	while (i < N as usize)
		invariant
			a.len() == N,
			sum.len() == 1,
			N > 0,
			N < 1000,
			i <= N as usize,
			forall|j: int| 0 <= j < N ==> a[j] == if j % 2 == 0 { 2int } else { 0int },
			i > 0 ==> sum[0] <= 2 * i as i32,
			i > 0 ==> sum[0] >= 0,
			i > 0 ==> sum[0] <= 2000,
		decreases N as usize - i,
	{
		if (i == 0) {
			sum.set(0, 0);
		} else {
			sum.set(0, sum[0] + a[i]);
		}
		i = i + 1;
	}
}
}