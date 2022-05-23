# 🧬 Pythogen: HTTP-clients generator for Python
Generator of python HTTP-clients from OpenApi specification based on `httpx` and `pydantic`.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## Features
- [Discriminator](/docs/discriminator.md)
- Sync and async clients
- Tracing
- Metrics

## Usage
Activate environment
```shell
rm -rf venv || true
python3.9 -m venv venv
source venv/bin/activate
make requirements
```
Generate clients
- Async
    ```shell
    python pythogen/entrypoint.py path/to/input/openapi.yaml path/to/output/client.py
    ```
- Sync
    ```shell
    python pythogen/entrypoint.py path/to/input/openapi.yaml path/to/output/client.py --sync
    ```

## For developers
- Activate environment
    ```shell
    rm -rf venv || true
    python3.9 -m venv venv
    source venv/bin/activate
    make requirements
    ```
- Make changes
- Execute `make clients-for-tests`
- Run tests `make tests-in-docker`
