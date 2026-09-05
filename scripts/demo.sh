#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Demonstracija rada celog sistema od pocetka do kraja.
#
#   ./scripts/demo.sh                     # podrazumevani NodePort-ovi
#   AUTH=http://localhost:30001 ./scripts/demo.sh
#
# Zahteva: curl, python3
# ---------------------------------------------------------------------------
set -euo pipefail

AUTH="${AUTH:-http://localhost:30001}"
EMPLOYEE="${EMPLOYEE:-http://localhost:30002}"
DIRECTOR="${DIRECTOR:-http://localhost:30003}"
GANACHE="${GANACHE:-http://localhost:30004}"

json() { python3 -c "import sys,json;print(json.dumps(json.load(sys.stdin),indent=2,ensure_ascii=False))"; }
field() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }

echo "==> 1. Registracija zaposlenog"
curl -s -o /dev/null -w "status=%{http_code}\n" -X POST "${AUTH}/register" \
  -H "Content-Type: application/json" \
  -d '{"forename":"Donald","surname":"Duck","email":"donald@gmail.com","password":"quackquack"}'

echo "==> 2. Prijava zaposlenog"
EMPLOYEE_TOKEN=$(curl -s -X POST "${AUTH}/login" -H "Content-Type: application/json" \
  -d '{"email":"donald@gmail.com","password":"quackquack"}' | field "['accessToken']")
echo "token: ${EMPLOYEE_TOKEN:0:32}..."

echo "==> 3. Prijava direktora"
DIRECTOR_TOKEN=$(curl -s -X POST "${AUTH}/login" -H "Content-Type: application/json" \
  -d '{"email":"onlymoney@gmail.com","password":"evenmoremoney"}' | field "['accessToken']")
echo "token: ${DIRECTOR_TOKEN:0:32}..."

echo "==> 4. Zaposleni predlaze kupovinu imovine"
curl -s -o /dev/null -w "status=%{http_code}\n" -X POST "${EMPLOYEE}/create_buy_order" \
  -H "Authorization: Bearer ${EMPLOYEE_TOKEN}" -H "Content-Type: application/json" \
  -d '{"name":"Zlatna poluga","categories":["metali","plemeniti metali"],
       "buying_price":10000,"info":{"tezina":{"vrednost":1000,"jedinica":"g"},"cistoca":999}}'

echo "==> 5. Direktor pregleda zahteve koji cekaju"
curl -s "${DIRECTOR}/pending_orders" -H "Authorization: Bearer ${DIRECTOR_TOKEN}" | json

ORDER_UUID=$(curl -s "${DIRECTOR}/pending_orders" -H "Authorization: Bearer ${DIRECTOR_TOKEN}" \
  | field "['orders'][0]['uuid']")
echo "uuid zahteva: ${ORDER_UUID}"

echo "==> 6. Ethereum racuni simulatora"
VOTERS=$(python3 - "$GANACHE" << 'PYEOF'
import json, sys, urllib.request
request = urllib.request.Request(
    sys.argv[1],
    data=json.dumps({"jsonrpc": "2.0", "method": "eth_accounts", "params": [], "id": 1}).encode(),
    headers={"Content-Type": "application/json"},
)
accounts = json.loads(urllib.request.urlopen(request).read())["result"]
print(json.dumps(accounts[1:4]))
PYEOF
)
echo "glasaci: ${VOTERS}"

echo "==> 7. Direktor odobrava zahtev i kreira pametni ugovor"
curl -s -X POST "${DIRECTOR}/decision" \
  -H "Authorization: Bearer ${DIRECTOR_TOKEN}" -H "Content-Type: application/json" \
  -d "{\"uuid\":\"${ORDER_UUID}\",\"voters\":${VOTERS}}" > /tmp/iep-transactions.json
json < /tmp/iep-transactions.json

echo "==> 8. Dva od tri zaposlena glasaju ZA (vecina je 2/3)"
python3 "$(dirname "$0")/vote.py" send --url "${GANACHE}" --account 1 --file /tmp/iep-transactions.json
python3 "$(dirname "$0")/vote.py" send --url "${GANACHE}" --account 2 --file /tmp/iep-transactions.json

echo "==> 9. Cekam nadzornu nit servisa direktora ..."
sleep 6

echo "==> 10. Zaposleni pretrazuje imovinu"
curl -s -X POST "${EMPLOYEE}/search" \
  -H "Authorization: Bearer ${EMPLOYEE_TOKEN}" -H "Content-Type: application/json" \
  -d '{"name":"Zlatna","info_filters":[{"field":"tezina.vrednost","operator":"gte","value":500}]}' | json

echo "==> 11. Izvestaj o poslovanju fonda"
curl -s "${DIRECTOR}/report" -H "Authorization: Bearer ${DIRECTOR_TOKEN}" | json

echo "==> Demonstracija zavrsena."
