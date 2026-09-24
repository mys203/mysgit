[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateLength(12, 128)]
    [string]$AdminPassword,

    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [int]$RedisPort = 6379
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $root '.venv\Scripts\python.exe'

function Test-PortListening([int]$port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $client.Connect('127.0.0.1', $port)
        return $true
    } catch {
        return $false
    } finally {
        $client.Dispose()
    }
}

if (-not (Test-Path -LiteralPath $python)) {
    throw "未找到后端虚拟环境：$python。请先创建 .venv 并安装 backend/requirements.txt。"
}

if (-not (Test-PortListening $RedisPort)) {
    $redis = Get-Command redis-server -ErrorAction SilentlyContinue
    if (-not $redis) {
        throw "未找到 redis-server，请先安装 Redis 或手动启动端口 $RedisPort。"
    }
    Start-Process -FilePath $redis.Source -ArgumentList '--port', $RedisPort, '--appendonly', 'no' -WindowStyle Hidden | Out-Null
    Start-Sleep -Milliseconds 800
}

if (-not (Test-PortListening $BackendPort)) {
    $env:APP_ENV = 'development'
    $env:DATABASE_URL = 'sqlite:///./recruit_local.db'
    $env:REDIS_URL = "redis://127.0.0.1:$RedisPort/0"
    $env:REDIS_REQUIRED = 'true'
    $env:REDIS_FALLBACK_ENABLED = 'false'
    $env:AUTO_CREATE_TABLES = 'true'
    $env:JWT_SECRET_KEY = 'Aa1!' + [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    $env:INITIAL_ADMIN_USERNAME = 'admin'
    $env:INITIAL_ADMIN_PASSWORD = $AdminPassword

    Start-Process -FilePath $python -ArgumentList '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', $BackendPort -WorkingDirectory $backend -WindowStyle Hidden | Out-Null
}

if (-not (Test-Path -LiteralPath (Join-Path $frontend 'node_modules'))) {
    $npm = (Get-Command npm.cmd).Source
    & $npm --prefix $frontend install
}

if (-not (Test-PortListening $FrontendPort)) {
    $npm = (Get-Command npm.cmd).Source
    Start-Process -FilePath $npm -ArgumentList 'run', 'dev', '--', '--host', '127.0.0.1', '--port', $FrontendPort -WorkingDirectory $frontend -WindowStyle Hidden | Out-Null
}

$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2 | Out-Null
        $backendReady = $true
        break
    } catch {}
}

[PSCustomObject]@{
    Frontend = "http://127.0.0.1:$FrontendPort"
    ApiDocs = "http://127.0.0.1:$BackendPort/docs"
    BackendReady = $backendReady
    RedisReady = (Test-PortListening $RedisPort)
    AdminUsername = 'admin'
    AdminPassword = $AdminPassword
} | Format-List
