use vstd::prelude::*;
fn main() {}
verus!{

pub fn myfun(a: &mut Vec<usize>, sum: &mut Vec<usize>, N: usize) 
	requires 
		old(a).len() == N,
		old(sum).len() == 1,
		N > 0,
	ensures
		sum[0] == 0,
{
	let mut i: usize = 0;
	while (i < N as usize)
	    invariant
	        i <= N,
	        a@.len() == N,
	        forall|j: int| 0 <= j < i ==> a@[j] == 0,
	    decreases
	        N - i,
	{
		a.set(i, i % 1 );
		i = i + 1;
	}

	i = 0;
	
	// Initialize sum[0] to 0 before the loop
	sum.set(0, 0);
	
	while (i < N as usize)
	    invariant
	        i <= N,
	        a@.len() == N,
	        sum@.len() == 1,
	        sum[0] == 0,
	        forall|j: int| 0 <= j < N ==> a@[j] == 0,
	    decreases
	        N - i,
	{
		if (i == 0) {
			sum.set(0, 0);
		} else {
			// Since i % 1 is always 0, a[i] is always 0, so sum[0] + a[i] is always sum[0]
			// This means sum[0] remains 0 throughout the loop
			assert(a@[i as int] == 0);
			sum.set(0, sum[0]);
		}
		i = i + 1;
	}
}
}