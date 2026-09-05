"""Kompajlira Voting.sol i cuva ABI i bytecode u contracts/Voting.json.

Skript se izvrsava u toku izgradnje Docker Image artefakta (docker build),
tako da kontejneru u toku rada nije potreban pristup internetu. Ukoliko
artefakt nije prisutan, aplikacija ce pokusati da ga napravi pri prvom
kreiranju ugovora.
"""

import json
import os
import pathlib
import sys

import solcx

SOLC_VERSION = os.environ.get("SOLC_VERSION", "0.8.19")
# byzantium se koristi zbog kompatibilnosti sa starijim ganache-cli simulatorom
# (noviji EVM-ovi koriste PUSH0 instrukciju koju simulator ne podrzava)
EVM_VERSION = os.environ.get("EVM_VERSION", "byzantium")

BASE_DIRECTORY = pathlib.Path(__file__).resolve().parent
SOURCE_PATH = BASE_DIRECTORY / "contracts" / "Voting.sol"
ARTIFACT_PATH = BASE_DIRECTORY / "contracts" / "Voting.json"


def ensure_solc():
    installed = [str(version) for version in solcx.get_installed_solc_versions()]
    if SOLC_VERSION not in installed:
        print(f"[compile] Instaliram solc {SOLC_VERSION} ...", flush=True)
        solcx.install_solc(SOLC_VERSION)


def compile_contract():
    ensure_solc()

    compiled = solcx.compile_files(
        [str(SOURCE_PATH)],
        output_values=["abi", "bin"],
        solc_version=SOLC_VERSION,
        evm_version=EVM_VERSION,
        optimize=True,
        allow_paths=[str(BASE_DIRECTORY)],
    )

    key = next(name for name in compiled if name.endswith(":Voting"))

    artifact = {
        "contractName": "Voting",
        "solcVersion": SOLC_VERSION,
        "evmVersion": EVM_VERSION,
        "abi": compiled[key]["abi"],
        "bytecode": "0x" + compiled[key]["bin"],
    }

    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2))
    print(f"[compile] Artefakt zapisan: {ARTIFACT_PATH}", flush=True)
    return artifact


if __name__ == "__main__":
    try:
        compile_contract()
    except Exception as exception:  # noqa: BLE001
        print(f"[compile] Greska pri kompajliranju: {exception}", flush=True)
        sys.exit(1)
