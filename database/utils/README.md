# Useful utilities for running the verification and parsing the results

## `autoverus.py`
This script is used to run AutoVerus for Verus-Bench and parse the verification result (i.e., proved tasks, llm query times and token consumption).

For example, for the `Misc` part:
```bash
$ python ./autoverus.py run-dir -o ../Verus-Bench/out/misc-autoverus ../Verus-Bench/code/benchmarks/Misc/unverified
```

> To enable the token consumption calculation, you need to apply the `database/utils/infer_changes.diff`


## `parse_verusbench.py`
This script is used to parse the verification result (i.e., detailed proved tasks) of KVerus for Verus-Bench:

```bash
$ python ./utils/parse_verusbench.py ./Verus-Bench/out/misc/prover
```


## `mathspec.py`
This script is used to run KVerus for Verus-Graph-Bench and parse the verification result (i.e., proved tasks, llm query times and token consumption).

```bash
$ python ./mathspec.py run
$ python ./mathspec.py parse
```


## `verus_cov.py`
This script is used to calculate coverage for verified code.

> This script depends on the Verus installed in `verified`  
> And API coverage depend on the json format documentation in the `verified`
>> Run `cargo dv doc --target ostd --json-output` to generate

```bash
$ python -m utils.verus_cov --line  # line coverage, writes logs/coverage_summary.csv
$ python -m utils.verus_cov --api   # API coverage, writes logs/ostd_api.json
```

## `parse_call_graph.py`
Script to analyze the call graph of Asterinas 0.16.0 (i.e., `database/mainline`).

> User need to run `PromeX-Rust` to gather call graph first. The call graphs should be in `database/mainline/out/preprocessor/call-kernel.json` and `database/mainline/out/preprocessor/call-ostd.json`

```bash
$ python -m utils.parse_call_graph
```

## `analyze_error.py`
Script to analyze the Verus log in the given log file.

```bash
$ python ./utils/analyze_error.py ./Verus-Bench/out/diffy-c37/log/final.log
```