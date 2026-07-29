# Reproducing Experiments from Our Paper

## Overview

As described in the evaluation section of [our paper](https://arxiv.org/abs/2605.03822), KVerus is evaluated on Rust/Verus formal verification targets. The artifact contains the following benchmark and example databases:

| Benchmark        | Source                                                                     | Location               |
| ---------------- | -------------------------------------------------------------------------- | ---------------------- |
| Verus-Bench      | [AutoVerus](https://arxiv.org/abs/2409.13082)                              | `database/Verus-Bench` |
| MBPP             | [AlphaVerus](https://arxiv.org/abs/2412.06176)                             | `database/MBPP`        |
| Human-Eval       | [AlphaVerus](https://arxiv.org/abs/2412.06176)                             | `database/HumanEval`   |
| CortenMM         | [VOSTD](https://github.com/asterinas/vostd)                                | `database/CortenMM`    |
| Memory Allocator | [VeruSage](https://arxiv.org/abs/2512.18436)                               | `database/sage`        |
| MathSpec-Bench   | [verus-mathspec-bench](https://github.com/rikosellic/verus-mathspec-bench) | `database/mathspec`    |

KVerus uses configurable LLM backends. The template configuration provides these default model placeholders:

- **Proof generation**: `claude sonnet 4.0`
- **Embedding model example**: `nomic-embed-text`

All experiments are configured through `config.toml` and a target-specific `fvts.toml` file.


## Reproduction
To facilitate reproducibility, we provide a suite of scripts for KVerus-related experiments. For the baseline tools, however, we do not provide ready-to-run scripts due to their complex setup procedures and dependencies. We recommend referring to the original papers and repositories for detailed execution instructions.

Please follow the steps in the sections below to set up and run the experiments.

### 0. Configure KVerus
Before running the experiments, you need to setup the environment and configure LLMs in `config.toml`. Refer to the [KVerus documentation](../../README.md) for detailed instructions.

### 1. Fetch Benchmark
To begin, fetch all the benchmarks using the `fetch_code.py` script:
```bash
$ python fetch_code.py
```

This will:
- Download the code of benchmarks
- Build the Verus tool needed

### 2. Comprehend Verus
```shell
$ python ./KVerus.py -D -F ./database/vstd/fvts.toml preprocess -F vstd
$ python ./KVerus.py -D -F ./database/verified/fvts.toml comprehend --fvt ostd
```

### 3. Run Verification
For quick reproduction, we provide pre-generated Verus files in the [examples directory](examples). The reported experiment results can be reproduced from these files by running:
```shell
$ python count_verified.py
```

The result should be like:
```
| INFO     | __main__:verify_target:136 - Target: database/experiment/examples/HumanEval
| INFO     | __main__:verify_target:154 - Total:  85
| SUCCESS  | __main__:verify_target:155 - Passed: 54
| ERROR    | __main__:verify_target:157 - Failed: 31

| INFO     | __main__:verify_target:136 - Target: database/experiment/examples/MBPP
| INFO     | __main__:verify_target:154 - Total:  78
| SUCCESS  | __main__:verify_target:155 - Passed: 65
| ERROR    | __main__:verify_target:157 - Failed: 13

| INFO     | __main__:verify_target:136 - Target: database/experiment/examples/Verus-Bench
| INFO     | __main__:verify_target:154 - Total:  150
| SUCCESS  | __main__:verify_target:155 - Passed: 132
| ERROR    | __main__:verify_target:157 - Failed: 18

| INFO     | __main__:main:202 - Aggregate:
| INFO     | __main__:main:203 - Total:  313
| SUCCESS  | __main__:main:204 - Passed: 251
| ERROR    | __main__:main:206 - Failed: 62
```

Alternatively, to rerun the full KVerus pipeline for the single-file benchmarks, use:

```shell
# For all single-file benchmarks
$ python run_single.py all

# For one single-file benchmark (e.g., HumanEval)
$ python run_single.py one HumanEval
```

This script runs KVerus proof generation for the selected benchmark(s), restores the corresponding `code/unverified` directory before each evaluation pass, parses the results with `database/utils/parse_verusbench.py`, and performs two additional reruns with `database/utils/rerun.py` to reproduce the reported retry-based results.
