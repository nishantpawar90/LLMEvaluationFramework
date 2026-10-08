<#
.SYNOPSIS
Downloads the MongoDB runtime required by this project into .mongodb/server.

.DESCRIPTION
This script is intentionally idempotent.  It installs the pinned MongoDB
version locally and creates the data directory, without adding binaries or
runtime state to source control.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$mongodbRoot = Join-Path $projectRoot '.mongodb'
$serverRoot = Join-Path $mongodbRoot 'server'
$dataRoot = Join-Path $mongodbRoot 'data'
$version = '4.4.29'
$archiveName = "mongodb-windows-x86_64-$version.zip"
$archivePath = Join-Path $mongodbRoot $archiveName
$runtimeDirectory = Join-Path $serverRoot "mongodb-win32-x86_64-windows-$version"
$mongodPath = Join-Path $runtimeDirectory 'bin\mongod.exe'
$downloadUrl = "https://fastdl.mongodb.org/windows/$archiveName"

if (Test-Path -LiteralPath $mongodPath) {
    Write-Host "MongoDB $version is already installed at $runtimeDirectory"
}
else {
    New-Item -ItemType Directory -Force -Path $mongodbRoot, $serverRoot | Out-Null
    Write-Host "Downloading MongoDB $version..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath

    Write-Host 'Extracting MongoDB runtime...'
    Expand-Archive -LiteralPath $archivePath -DestinationPath $serverRoot -Force
    Remove-Item -LiteralPath $archivePath -Force

    if (-not (Test-Path -LiteralPath $mongodPath)) {
        throw "MongoDB download completed, but mongod.exe was not found at $mongodPath"
    }
}

New-Item -ItemType Directory -Force -Path $dataRoot | Out-Null

Write-Host ''
Write-Host 'MongoDB runtime is ready. Start it in a separate PowerShell window with:'
Write-Host "& '$mongodPath' --dbpath '$dataRoot' --bind_ip 127.0.0.1 --port 27017 --logpath '$(Join-Path $mongodbRoot 'mongod.log')'"
