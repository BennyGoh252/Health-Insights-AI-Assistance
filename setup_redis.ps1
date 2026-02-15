#!/bin/bash
# Setup Redis on Windows
# This script downloads the pre-built Windows Redis binary

$RedisVersion = "7.2.4"
$RedisZip = "redis-$RedisVersion-windows-x64.zip"
$RedisUrl = "https://github.com/microsoftarchive/redis/releases/download/win-$RedisVersion/redis-$RedisVersion-windows-x64.zip"
$DownloadPath = "$env:USERPROFILE\Downloads\$RedisZip"
$ExtractPath = "C:\Redis"

Write-Host "Downloading Redis for Windows..."
Write-Host "URL: $RedisUrl"

# Check if directory exists
if (-not (Test-Path $ExtractPath)) {
    New-Item -ItemType Directory -Path $ExtractPath | Out-Null
}

# Download
try {
    Invoke-WebRequest -Uri $RedisUrl -OutFile $DownloadPath -ErrorAction Stop
    Write-Host "Downloaded to: $DownloadPath"
} catch {
    Write-Host "Download failed. Trying alternative method..."
    Write-Host "You can manually download from: https://github.com/microsoftarchive/redis/releases"
    exit 1
}

# Extract
Write-Host "Extracting Redis..."
Expand-Archive -Path $DownloadPath -DestinationPath $ExtractPath -Force

Write-Host "Redis installed to: $ExtractPath"
Write-Host ""
Write-Host "To start Redis, run:"
Write-Host "  cd $ExtractPath"
Write-Host "  .\redis-server.exe"
Write-Host ""
Write-Host "In another terminal, you can test it with:"
Write-Host "  cd $ExtractPath"
Write-Host "  .\redis-cli.exe"
