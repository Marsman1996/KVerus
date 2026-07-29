use vstd::prelude::*;
fn main() {}
verus!{
pub fn myfun(a: &mut Vec<i32>, sum: &mut Vec<i32>, N: i32)
	requires
		N > 0,
		old(a).len() == N as usize,
		old(sum).len() == 1,
		N < 1000,
	ensures
		sum[0] == 5 * N,
{
	let mut i: usize = 0;
	sum.set(0, 0);

	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		i <= N as usize,
		forall|j: usize| j < i ==> a@[j as int] == 1,
		decreases (N as usize - i)
	{
		a.set(i, 1);
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		i <= N as usize,
		forall|j: usize| j < i ==> a@[j as int] == 5,
		forall|j: usize| i < j && j < N as usize ==> a@[j as int] == 1,
		decreases (N as usize - i)
	{
		if (a[i] == 1) {
			a.set(i, a[i] + 4);
		} else {
			a.set(i, a[i] - 1);
		}
		i = i + 1;
	}

	i = 0;
	while (i < N as usize)
	invariant
		N > 0,
		a.len() == N as usize,
		sum.len() == 1,
		i <= N as usize,
		sum[0] == 5 * i as i32,
		forall|j: usize| j < N as usize ==> a@[j as int] == 5,
		0 <= sum[0] <= 5 * N,  // Added bound to prevent overflow
		N < 1000,  // Added from requires
		decreases (N as usize - i)
	{
		assert(a@[i as int] == 5);  // Added to help the verifier
		
		// Prove that the addition won't overflow
		assert(sum[0] <= 5 * N - 5); // Current sum is at most 5*(N-1)
		assert(a@[i as int] == 5);
		assert(sum[0] + a@[i as int] <= 5 * N); // Sum after addition won't exceed 5*N
		
		sum.set(0, sum[0] + a[i]);
		
		// Prove the assertion about the updated sum
		assert(sum[0] == 5 * i as i32 + 5);
		assert(5 * i as i32 + 5 == 5 * (i + 1) as i32);
		assert(sum[0] == 5 * (i + 1) as i32);  // Added to help the verifier
		
		i = i + 1;
	}
}
}