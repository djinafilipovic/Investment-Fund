# Sistem za upravljanje investicionim fondom

Projekat iz predmeta **Internet i elektronsko poslovanje**. Sistem je realizovan kao
skup mikroservisa u programskom jeziku Python (Flask), koji se pokrecu pomocu
Kubernetes alata. Odobravanje zahteva je implementirano pomocu pametnog ugovora
na Ethereum Blockchain platformi (ganache-cli simulator).

---

## 1. Sadrzaj repozitorijuma

```
iep-investment-fund/
├── authentication/            # veb servis za upravljanje korisnickim nalozima
│   ├── application/
│   │   ├── configuration.py   # konfiguracija iz varijabli okruzenja
│   │   ├── models.py          # SQLAlchemy modeli (User, Role)
│   │   ├── responses.py
│   │   └── validation.py
│   ├── authentication.py      # /register, /login, /delete
│   ├── migrate.py             # inicijalizacija baze + pocetni direktor
│   ├── requirements.txt
│   └── Dockerfile
│
├── employee/                  # veb servis za zaposlene
│   ├── application/
│   │   ├── configuration.py
│   │   ├── db.py              # PyMongo i Redis klijenti
│   │   ├── security.py        # provera tokena i uloge
│   │   ├── serialization.py   # ISO 8601 datumi, serijalizacija imovine
│   │   └── validation.py
│   ├── employee.py            # /search, /create_buy_order, /create_sell_order
│   ├── requirements.txt
│   └── Dockerfile
│
├── director/                  # veb servis za direktora
│   ├── application/
│   │   ├── blockchain.py      # Web3 integracija, kreiranje ugovora
│   │   ├── orders.py          # obrada odobrenih zahteva, izvestaj
│   │   ├── watcher.py         # nadzorna nit koja prati glasanje
│   │   └── ...
│   ├── contracts/Voting.sol   # pametni ugovor za vecinsko glasanje
│   ├── contracts/Voting.json  # ABI i bytecode (rezultat kompajliranja)
│   ├── compile_contract.py    # kompajliranje ugovora (py-solc-x)
│   ├── director.py            # /pending_orders, /decision, /report
│   ├── requirements.txt
│   └── Dockerfile
│
├── kubernetes/                # manifesti za pokretanje celog sistema
│   ├── 00-config.yaml         # ConfigMap + Secret
│   ├── 01-storage.yaml        # PersistentVolumeClaim objekti
│   ├── 02-authentication-db.yaml   # MySQL
│   ├── 03-fund-db.yaml             # MongoDB
│   ├── 04-order-cache.yaml         # Redis
│   ├── 05-ganache.yaml             # Ethereum simulator
│   ├── 06-authentication.yaml
│   ├── 07-employee.yaml            # 3 replike
│   └── 08-director.yaml
│
├── scripts/
│   └── vote.py                # slanje glasa nad pametnim ugovorom
│
├── docker-compose.yml         # pomocna konfiguracija za lokalni razvoj
└── README.md
```

---

## 2. Sta je potrebno instalirati

### 2.1 Obavezno

| Alat | Minimalna verzija | Cemu sluzi |
|------|-------------------|------------|
| Docker Engine / Docker Desktop | 24.x | izgradnja i pokretanje kontejnera |
| kubectl | 1.28 | komunikacija sa Kubernetes klasterom |
| minikube (ili Docker Desktop Kubernetes / kind) | 1.32 | lokalni Kubernetes klaster |
| Python | 3.11 | lokalni razvoj i pomocni skriptovi |
| curl | bilo koja | testiranje veb servisa |

### 2.2 Instalacija — Windows

```powershell
# Docker Desktop (ukljucuje i kubectl)
winget install -e --id Docker.DockerDesktop

# minikube
winget install -e --id Kubernetes.minikube

# Python
winget install -e --id Python.Python.3.11
```

> U Docker Desktop podesavanjima (*Settings → Kubernetes*) moguce je ukljuciti
> ugradjeni Kubernetes klaster i tada minikube nije potreban.

> Sve komande za izgradnju i pokretanje sistema navedene su u sekciji 3 i
> izvrsavaju se direktno (`docker` i `kubectl`), bez pomocnih skripti.
> Arhitektura racunara nije prepreka — svi Docker Image artefakti i pametni
> ugovor se grade i pokrecu identicno na `amd64` (vecina Windows racunara)
> kao i na Linux-u.

### 2.3 Instalacija — Linux (Debian / Ubuntu)

```bash
# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"      # nakon ovoga se odjaviti i prijaviti

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Python
sudo apt-get install -y python3.11 python3.11-venv python3-pip
```

### 2.4 Instalacija — macOS

```bash
brew install --cask docker
brew install kubectl minikube python@3.11
```

### 2.5 Python zavisnosti za pomocne skriptove

Skript `scripts/vote.py` se izvrsava na racunaru (van kontejnera):

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install web3==6.20.3
```

### 2.6 Docker Image artefakti koji se preuzimaju sa Docker Hub-a

Preuzimaju se automatski prilikom pokretanja sistema:

- `mysql:8.0`
- `mongo:7.0`
- `redis:7.2-alpine`
- `trufflesuite/ganache-cli:v6.12.2`
- `python:3.11-slim` (osnovni image za sopstvene servise)

---

## 3. Pokretanje sistema pomocu Kubernetes alata

Sistem se pokrece na ugradjenom Kubernetes klasteru Docker Desktop-a
(*Settings → Kubernetes → Enable Kubernetes*):

```powershell
# 1) provera da je klaster spreman (status mora biti "Ready")
kubectl get nodes

# 2) izgradnja Docker Image artefakata
docker build -t iep/authentication:v1 .\authentication
docker build -t iep/employee:v1 .\employee
docker build -t iep/director:v1 .\director

# 3) pokretanje sistema
kubectl apply -f kubernetes\

# 4) prebacivanje servisa na izgradjene oznake
kubectl set image deployment/authentication authentication=iep/authentication:v1
kubectl set image deployment/employee employee=iep/employee:v1
kubectl set image deployment/director director=iep/director:v1

# 5) provera stanja (sve treba da bude 1/1 Running)
kubectl get pods
kubectl get svc
```

> **Zasto korak 4.** Kubernetes klaster ima sopstveno skladiste image-a
> (`containerd`), odvojeno od Docker-ovog. Uz oznaku `latest` i
> `imagePullPolicy: IfNotPresent`, klaster zadrzi ranije kesiranu kopiju i ne
> primeti novu izgradnju — servis tada radi sa starim kodom. Zato se svaka
> izgradnja oznacava novom oznakom (`v1`, `v2`, ...) i servisi se eksplicitno
> prebacuju na nju. Sve je lokalno — pristup internetu nije potreban.

### 3.0 Izmena servisa nakon pokretanja

Posle izmene koda dovoljno je ponovo izgraditi **samo taj servis**, uz **novu**
oznaku, i prebaciti deployment na nju:

```powershell
docker build -t iep/employee:v2 .\employee
kubectl set image deployment/employee employee=iep/employee:v2
kubectl rollout status deployment/employee

# provera da pod stvarno ima novi kod
kubectl exec deploy/employee -- grep -n "<nesto iz izmene>" /app/employee.py
```

Ovo radi i bez pristupa internetu: Docker kesira sloj sa `pip install`, pa se
zavisnosti ne preuzimaju ponovo sve dok se `requirements.txt` ne menja.

### 3.1 Adrese servisa

Servisi su izlozeni preko `NodePort` tipa:

| Servis | NodePort | Adresa |
|--------|----------|--------|
| authentication | 30001 | `http://localhost:30001` |
| employee | 30002 | `http://localhost:30002` |
| director | 30003 | `http://localhost:30003` |
| ganache (RPC) | 30004 | `http://localhost:30004` |

Novije verzije Docker Desktop-a **ne prosledjuju** `NodePort` na `localhost`
automatski. Provera:

```powershell
curl http://localhost:30001/health
```

Ako odgovor izostane (`Connection refused`), otvaraju se tuneli — svaka
naredba u **zasebnom** prozoru, koji ostaje otvoren:

```powershell
kubectl port-forward svc/authentication 30001:5000
kubectl port-forward svc/employee 30002:5000
kubectl port-forward svc/director 30003:5000
kubectl port-forward svc/ganache 30004:8545
```

> Tunel se prekida kada se pod restartuje (npr. posle `kubectl set image`), pa
> ga tada treba pokrenuti ponovo.

### 3.2 Zaustavljanje

```powershell
kubectl delete -f kubernetes\

# uklanjanje i trajnih podataka iz baza:
kubectl delete pvc authentication-db-data fund-db-data order-cache-data
```

---

## 4. Pokretanje za lokalni razvoj (Docker Compose)

```bash
docker compose up --build
```

Adrese: authentication `http://localhost:5001`, employee `http://localhost:5002`,
director `http://localhost:5003`, ganache `http://localhost:8545`.

---

## 5. Inicijalno stanje sistema

Prilikom pokretanja, `initContainer` u okviru deployment-a `authentication`
izvrsava skript `migrate.py`, koji:

1. ceka da relaciona baza podataka postane dostupna;
2. kreira sve potrebne tabele (`roles`, `users`);
3. dodaje uloge `director` i `employee`;
4. dodaje pocetni nalog direktora fonda:

```json
{
  "forename": "Scrooge",
  "surname": "McDuck",
  "email": "onlymoney@gmail.com",
  "password": "evenmoremoney"
}
```

Skript je idempotentan, pa ponovno pokretanje sistema nece napraviti duplikate.

---

## 6. Pregled funkcionalnosti

### 6.1 Servis `authentication` (port 30001)

| Adresa | Tip | Opis |
|--------|-----|------|
| `/register` | POST | registracija korisnika sa ulogom zaposlenog |
| `/login` | POST | prijava, vraca `accessToken` (vazi 1 sat) |
| `/delete` | POST | brisanje sopstvenog naloga (zahteva token) |

### 6.2 Servis `employee` (port 30002, 3 replike)

| Adresa | Tip | Opis |
|--------|-----|------|
| `/search` | POST | pretraga imovine (uz `info_filters` nad ugnjezdenim poljima) |
| `/create_buy_order` | POST | predlog kupovine imovine (upisuje se u Redis) |
| `/create_sell_order` | POST | predlog prodaje imovine (upisuje se u Redis) |

### 6.3 Servis `director` (port 30003)

| Adresa | Tip | Opis |
|--------|-----|------|
| `/pending_orders` | GET | zahtevi koji cekaju odluku |
| `/decision` | POST | kreira pametni ugovor za glasanje i vraca dve transakcije |
| `/decision_basic` | POST | osnovna varijanta odlucivanja, bez glasanja |
| `/report` | GET | statistika po kategorijama (`spent`, `earned`) |

> `/decision_basic` je zadrzan radi demonstracije obaveznog dela projekta;
> prosirena varijanta sa glasanjem nalazi se na `/decision`, kako je i trazeno.

Svaki servis ima i `/health` adresu koju koriste `readinessProbe` i `livenessProbe`.

---

## 7. Primeri zahteva

```bash
AUTH=http://localhost:30001
EMPLOYEE=http://localhost:30002
DIRECTOR=http://localhost:30003
```

**Registracija i prijava**

```bash
curl -X POST "$AUTH/register" -H "Content-Type: application/json" \
  -d '{"forename":"Donald","surname":"Duck","email":"donald@gmail.com","password":"quackquack"}'

TOKEN=$(curl -s -X POST "$AUTH/login" -H "Content-Type: application/json" \
  -d '{"email":"donald@gmail.com","password":"quackquack"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['accessToken'])")
```

**Predlog kupovine**

```bash
curl -X POST "$EMPLOYEE/create_buy_order" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Zlatna poluga","categories":["metali"],"buying_price":10000,
       "info":{"tezina":{"vrednost":1000,"jedinica":"g"}}}'
```

**Pretraga sa filterima nad ugnjezdenim poljima**

```bash
curl -X POST "$EMPLOYEE/search" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Zlatna","category":"metali",
       "buying_date":"2020-01-01T00:00:00.000Z",
       "info_filters":[{"field":"tezina.vrednost","operator":"gte","value":500}]}'
```

**Izvestaj direktora**

```bash
DTOKEN=$(curl -s -X POST "$AUTH/login" -H "Content-Type: application/json" \
  -d '{"email":"onlymoney@gmail.com","password":"evenmoremoney"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['accessToken'])")

curl "$DIRECTOR/report" -H "Authorization: Bearer $DTOKEN"
```

---

## 8. Odobravanje zahteva glasanjem

1. Direktor poziva `/decision` sa identifikatorom zahteva i listom Ethereum adresa
   koje smeju da glasaju (broj adresa mora biti **neparan**).
2. Servis kreira novi objekat pametnog ugovora `Voting` na simulatoru. Naknadu za
   kreiranje placa prvi racun koji simulator otkljuca prilikom pokretanja.
3. Odgovor sadrzi dve nepotpisane transakcije:

```json
{
  "approve_transaction": {"to": "0x...", "data": "0x...", "gas": 200000, "gasPrice": 20000000000, "value": 0, "chainId": 1337},
  "reject_transaction":  {"to": "0x...", "data": "0x...", "gas": 200000, "gasPrice": 20000000000, "value": 0, "chainId": 1337}
}
```

4. Zaposleni glasa slanjem jedne od transakcija sa svog racuna:

```bash
# spisak racuna simulatora
python scripts/vote.py accounts --url http://localhost:30004

# glasanje racunom sa indeksom 1 (glas ZA)
curl -s -X POST "$DIRECTOR/decision" -H "Authorization: Bearer $DTOKEN" \
  -H "Content-Type: application/json" \
  -d '{"uuid":"...","voters":["0x...","0x...","0x..."]}' > tx.json

python scripts/vote.py send --url http://localhost:30004 --account 1 --file tx.json
python scripts/vote.py send --url http://localhost:30004 --account 2 --file tx.json          # glas ZA
python scripts/vote.py send --url http://localhost:30004 --account 3 --file tx.json --reject # glas PROTIV
```

5. Nadzorna nit u servisu direktora periodicno proverava stanje svakog aktivnog
   ugovora. Kada broj glasova dostigne vecinu (`n / 2 + 1`):
   - ako je zahtev **odobren**, imovina se upisuje / azurira u MongoDB bazi, a
     zahtev se uklanja iz Redis servisa;
   - ako je zahtev **odbijen**, samo se uklanja iz Redis servisa.

### Ogranicenja koja ugovor sam proverava

| Situacija | Poruka |
|-----------|--------|
| glasa racun koji nije u listi `voters` | `Invalid address.` |
| glasanje nakon zavrsetka | `Voting ended.` |
| glasac vec glasao | `Already voted.` |
| paran broj glasaca (pri kreiranju) | `Even number of voters.` |

### Kompletna demonstracija

Ceo tok (registracija → prijava → predlog kupovine → pregled zahteva →
kreiranje ugovora → glasanje → pretraga → izvestaj) pokriven je automatskim
testovima iz direktorijuma `iep_grader`:

```powershell
cd iep_grader
pytest -q --type all `
  --authentication-url http://localhost:30001 `
  --employee-url http://localhost:30002 `
  --director-url http://localhost:30003 `
  --provider-url http://localhost:30004 `
  --jwt-secret 5f2b8c1a4d7e9f0b3c6a8d1e4f7b2c5a8d1e4f7b2c5a8d1e `
  --roles-field role --employee-role employee --director-role director `
  --with-authentication --with-blockchain --wait-for-services
```

Pojedinacni koraci mogu se izvrsiti i rucno, `curl` naredbama iz sekcije 7.

---

## 9. Struktura podataka

### 9.1 MySQL (`iep_users`)

- `roles(id, name)` — `director`, `employee`
- `users(id, forename, surname, email, password, role_id)`

Lozinke se cuvaju kao PBKDF2-SHA256 hash (`werkzeug.security`), nikada kao cist tekst.

### 9.2 MongoDB (`fund.assets`)

```json
{
  "_id": ObjectId("..."),
  "name": "Zlatna poluga",
  "categories": ["metali", "plemeniti metali"],
  "buying_price": 10000,
  "buying_date": ISODate("..."),
  "selling_price": 20000,
  "selling_date": ISODate("..."),
  "info": { "tezina": { "vrednost": 1000, "jedinica": "g" } }
}
```

Polja `selling_price` i `selling_date` postoje samo kod prodate imovine.

### 9.3 Redis

| Kljuc | Tip | Sadrzaj |
|-------|-----|---------|
| `pending_orders` | hash | `uuid → JSON zahteva` |
| `voting_contracts` | hash | `uuid → {address, order}` (aktivni ugovori) |
| `processed_order:<uuid>` | string | zastita od dvostruke obrade istog zahteva |

---

## 10. Napomene o implementaciji

- **Upiti se izvrsavaju u bazi.** Pretraga imovine, provera postojanja korisnika i
  izvestaj o poslovanju realizovani su kroz SQLAlchemy upite, odnosno PyMongo
  `find` i `aggregate` operacije; ni u jednom slucaju se ne ucitava cela kolekcija
  da bi se filtrirala u Pythonu.
- **Izvestaj** koristi agregacioni cevovod: `$unwind` nad kategorijama, `$group`
  po kategoriji, pa `$sort` po `earned` opadajuce, `spent` rastuce i `category`
  rastuce.
- **Sortiranje i filtriranje datuma.** Datumi se u bazi cuvaju kao UTC vrednosti, a
  u odgovorima se formatiraju u ISO 8601 obliku sa milisekundama i `Z` sufiksom.
- **Konfiguracija.** Nijedna adresa, lozinka ni naziv baze nije upisan u kod —
  sve dolazi iz `ConfigMap` i `Secret` objekata putem varijabli okruzenja.
- **Pametni ugovor** je kompajliran unapred, jednokratno
  (`solc 0.8.19`, ciljni EVM `byzantium` zbog kompatibilnosti sa `ganache-cli`).
  Rezultat su ABI i EVM bytecode, sto ne zavisi od arhitekture racunara, pa
  Docker Image samo preuzima gotov artefakt `director/contracts/Voting.json`.
  Zahvaljujuci tome za izgradnju image-a nije potreban ni kompajler ni pristup
  internetu. Samo kompajliranje se izvrsava u jednokratnom `linux/amd64`
  kontejneru, jer Solidity tim ne objavljuje `solc 0.8.19` za `linux/arm64`.
- **Servis direktora radi u jednoj replici sa jednim gunicorn radnikom**, kako bi
  postojala tacno jedna nadzorna nit. Dodatno, obrada zahteva je zasticena
  `SET NX` zakljucavanjem u Redis servisu, pa je bezbedna i pri vecem broju replika.
- **Servis za zaposlene radi u tri replike** i ne cuva stanje u memoriji, pa se
  zahtevi mogu obradjivati paralelno.

---

## 11. Resavanje problema

| Problem | Resenje |
|---------|---------|
| `ImagePullBackOff` za `iep/*` | image sa tom oznakom ne postoji — proveriti `docker images` i ponoviti `docker build` pa `kubectl set image` |
| Servis radi sa starim kodom nakon izmene | klaster koristi kesirani image — izgraditi sa **novom** oznakom (`v2`, `v3`, ...) i pokrenuti `kubectl set image` |
| `contracts/Voting.json ne postoji` | artefakt ugovora nedostaje — vratiti ga iz sistema za verzionisanje (`git checkout director/contracts/Voting.json`) |
| Pod `authentication` u stanju `Init:0/1` | ceka MySQL; pratiti `kubectl logs deploy/authentication -c migrate` |
| `Missing Authorization Header` | nije poslato zaglavlje `Authorization: Bearer <token>` |
| `403 Forbidden.` | koriscen je token pogresne uloge (npr. token zaposlenog na servisu direktora) |
| Greska pri kreiranju ugovora | proveriti da li ganache radi: `kubectl logs deploy/ganache` |
| Glasanje ne zavrsava zahtev | pogledati `kubectl logs deploy/director` — nadzorna nit ispisuje ishod svakog glasanja |
| Nedovoljno resursa u klasteru | `minikube start --cpus=4 --memory=6144` |

Korisne komande:

```bash
kubectl get pods -w
kubectl logs -f deploy/director
kubectl logs -f deploy/employee --all-containers
kubectl exec -it deploy/order-cache -- redis-cli hgetall pending_orders
kubectl exec -it deploy/fund-db -- mongosh fund --eval "db.assets.find().pretty()"
```
