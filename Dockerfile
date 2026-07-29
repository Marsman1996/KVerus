ARG RUST_VERSION=1.91.0
FROM rust:${RUST_VERSION} AS rust-toolchain

FROM ubuntu:24.04

# install system dependencies
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get -y install --no-install-recommends \
    git \
    vim \
    build-essential \
    cmake \
    curl \
    pkg-config \
    libssl-dev \
    python-is-python3 \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# install Rust toolchain (required for building promex-verus and Verus)
COPY --from=rust-toolchain /usr/local/cargo /usr/local/cargo
COPY --from=rust-toolchain /usr/local/rustup /usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo \
    RUSTUP_HOME=/usr/local/rustup \
    PATH="/usr/local/cargo/bin:${PATH}"

# set work directory
COPY . /kverus
WORKDIR /kverus

# install Python dependencies using uv (handles workspace members like promex-verus)
RUN uv sync --no-dev --no-editable

# build PromeX-Verus preprocessor binary (Rust -> release binary)
RUN chmod +x ./scripts/setup.sh && ./scripts/setup.sh

# fetch all code
RUN uv run database/experiment/fetch_code.py
