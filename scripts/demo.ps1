# ---------------------------------------------------------------------------
# Demonstracija rada celog sistema od pocetka do kraja (Windows/PowerShell).
#
#   .\scripts\demo.ps1
#   $env:AUTH = "http://localhost:30001"; .\scripts\demo.ps1
#
# Zahteva: Python 3.11 na PATH kao "python" (koristi ga scripts\vote.py)
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Stop"

$Auth     = if ($env:AUTH)     { $env:AUTH }     else { "http://localhost:30001" }
$Employee = if ($env:EMPLOYEE) { $env:EMPLOYEE } else { "http://localhost:30002" }
$Director = if ($env:DIRECTOR) { $env:DIRECTOR } else { "http://localhost:30003" }
$Ganache  = if ($env:GANACHE)  { $env:GANACHE }  else { "http://localhost:30004" }

Write-Host "==> 1. Registracija zaposlenog"
try {
    Invoke-RestMethod -Method Post -Uri "$Auth/register" -ContentType "application/json" -Body (
        @{ forename = "Donald"; surname = "Duck"; email = "donald@gmail.com"; password = "quackquack" } | ConvertTo-Json
    ) | Out-Null
    Write-Host "status=200"
} catch {
    Write-Host "status=$([int]$_.Exception.Response.StatusCode)"
}

Write-Host "==> 2. Prijava zaposlenog"
$employeeLogin = Invoke-RestMethod -Method Post -Uri "$Auth/login" -ContentType "application/json" -Body (
    @{ email = "donald@gmail.com"; password = "quackquack" } | ConvertTo-Json
)
$EmployeeToken = $employeeLogin.accessToken
Write-Host "token: $($EmployeeToken.Substring(0,32))..."

Write-Host "==> 3. Prijava direktora"
$directorLogin = Invoke-RestMethod -Method Post -Uri "$Auth/login" -ContentType "application/json" -Body (
    @{ email = "onlymoney@gmail.com"; password = "evenmoremoney" } | ConvertTo-Json
)
$DirectorToken = $directorLogin.accessToken
Write-Host "token: $($DirectorToken.Substring(0,32))..."

Write-Host "==> 4. Zaposleni predlaze kupovinu imovine"
$buyOrderBody = @{
    name          = "Zlatna poluga"
    categories    = @("metali", "plemeniti metali")
    buying_price  = 10000
    info          = @{ tezina = @{ vrednost = 1000; jedinica = "g" }; cistoca = 999 }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri "$Employee/create_buy_order" `
    -Headers @{ Authorization = "Bearer $EmployeeToken" } -ContentType "application/json" -Body $buyOrderBody | Out-Null
Write-Host "status=200"

Write-Host "==> 5. Direktor pregleda zahteve koji cekaju"
$pending = Invoke-RestMethod -Uri "$Director/pending_orders" -Headers @{ Authorization = "Bearer $DirectorToken" }
$pending | ConvertTo-Json -Depth 5
$OrderUuid = $pending.orders[0].uuid
Write-Host "uuid zahteva: $OrderUuid"

Write-Host "==> 6. Ethereum racuni simulatora"
$rpcBody = @{ jsonrpc = "2.0"; method = "eth_accounts"; params = @(); id = 1 } | ConvertTo-Json
$rpcResponse = Invoke-RestMethod -Method Post -Uri $Ganache -ContentType "application/json" -Body $rpcBody
$Voters = $rpcResponse.result[1..3]
Write-Host "glasaci: $($Voters -join ', ')"

Write-Host "==> 7. Direktor odobrava zahtev i kreira pametni ugovor"
$decisionBody = @{ uuid = $OrderUuid; voters = $Voters } | ConvertTo-Json
$transactions = Invoke-RestMethod -Method Post -Uri "$Director/decision" `
    -Headers @{ Authorization = "Bearer $DirectorToken" } -ContentType "application/json" -Body $decisionBody
$transactions | ConvertTo-Json -Depth 5

$TransactionsFile = Join-Path ([System.IO.Path]::GetTempPath()) "iep-transactions.json"
$transactions | ConvertTo-Json -Depth 5 | Set-Content -Path $TransactionsFile

Write-Host "==> 8. Dva od tri zaposlena glasaju ZA (vecina je 2/3)"
python (Join-Path $PSScriptRoot "vote.py") send --url $Ganache --account 1 --file $TransactionsFile
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python (Join-Path $PSScriptRoot "vote.py") send --url $Ganache --account 2 --file $TransactionsFile
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> 9. Cekam nadzornu nit servisa direktora ..."
Start-Sleep -Seconds 6

Write-Host "==> 10. Zaposleni pretrazuje imovinu"
$searchBody = @{
    name         = "Zlatna"
    info_filters = @(@{ field = "tezina.vrednost"; operator = "gte"; value = 500 })
} | ConvertTo-Json -Depth 5
$searchResult = Invoke-RestMethod -Method Post -Uri "$Employee/search" `
    -Headers @{ Authorization = "Bearer $EmployeeToken" } -ContentType "application/json" -Body $searchBody
$searchResult | ConvertTo-Json -Depth 5

Write-Host "==> 11. Izvestaj o poslovanju fonda"
$report = Invoke-RestMethod -Uri "$Director/report" -Headers @{ Authorization = "Bearer $DirectorToken" }
$report | ConvertTo-Json -Depth 5

Write-Host "==> Demonstracija zavrsena."
