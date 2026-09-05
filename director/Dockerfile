FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOLCX_BINARY_PATH=/opt/solc

WORKDIR /app

# gcc/g++ su potrebni za pojedine zavisnosti biblioteke web3
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/solc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pametni ugovor je vec kompajliran skriptom scripts/compile-contract.sh, pa se
# ovde samo preuzima gotov artefakt (ABI + EVM bytecode). Zahvaljujuci tome za
# izgradnju image-a nije potreban ni solc ni pristup internetu, a bytecode ne
# zavisi od arhitekture racunara na kojem se image gradi.
RUN test -f contracts/Voting.json \
    || (echo "GRESKA: contracts/Voting.json ne postoji - pokreni ./scripts/compile-contract.sh" >&2 && exit 1)

EXPOSE 5000

# Pokrece se kao jedan proces, kako bi postojala tacno jedna nadzorna nit
# za glasanje (zato je i debug iskljucen u director.py - ukljucen debug bi
# pokrenuo auto-reloader, a s njim i drugi proces sa svojom nitju).
CMD ["python", "director.py"]
