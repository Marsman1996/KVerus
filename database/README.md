# Formal Verification Targets Database

This directory contains several libraries that are configured to be verified using KVerus.

## Libraries
Typically, each library is in a separate subdirectory, with `fetch.sh` and `fvts.toml` files inside, which should be executed in order:

1. `fetch.sh` downloads the library source code.
2. `fvts.toml` is the configuration file for the KVerus. After the library is fetched, run:
    - `./KVerus.py -F database/xxx/fvts.toml xxx`
