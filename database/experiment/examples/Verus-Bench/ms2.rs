use vstd::prelude::*;
fn main() {}
verus!{

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize) 
	requires 
		old(a).len() == N,
		old(sum).len() == 1,
		N > 0,
	ensures
		sum[0] <= N,
{
	let mut i: usize = 0;
	while (i < N as usize)
	invariant
		i <= N,
		a.len() == N,
		forall |j: int| 0 <= j < i ==> a@[j] <= 1,
	decreases
		N - i,
	{
		a.set(i, i % 2 );
		i = i + 1;
	}

	i = 0;
	sum.set(0, 0);
	
	while (i < N as usize)
	invariant
		i <= N,
		sum.len() == 1,
		a.len() == N,
		sum[0] <= i,
		i == 0 ==> sum[0] == 0,
		forall |j: int| 0 <= j < N ==> a@[j] <= 1,
	decreases
		N - i,
	{
		if (i == 0) {
			sum.set(0, 0);
		} else {
			assert(a@[i as int] <= 1); // a[i] is either 0 or 1 (i % 2)
			sum.set(0, sum[0] + a[i]);
		}
		i = i + 1;
	}
}
}