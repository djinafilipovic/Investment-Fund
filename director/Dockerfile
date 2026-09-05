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

# jedan radnik, kako bi u procesu postojala samo jedna nadzorna nit za glasanje
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", \
     "--access-logfile", "-", "director:application"]
