<#
.SYNOPSIS
    Package a modlet for release (Windows).

.EXAMPLE
    .\tools\build.ps1 TheEighthDay   # -> dist\TheEighthDay-0.1.0.zip
    .\tools\build.ps1                # builds every modlet

.NOTES
    The zip contains the modlet folder at its root so players extract straight into
    Mods\. Docs are excluded from the shipped zip - they belong on GitHub.
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Modlets
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not $Modlets -or $Modlets.Count -eq 0) {
    $Modlets = Get-ChildItem -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName 'ModInfo.xml') } |
        Select-Object -ExpandProperty Name
}

if (-not $Modlets) {
    throw 'No modlets found (looking for top-level dirs containing ModInfo.xml).'
}

$dist = Join-Path $repoRoot 'dist'
New-Item -ItemType Directory -Force -Path $dist | Out-Null

foreach ($modlet in $Modlets) {
    $modInfoPath = Join-Path $modlet 'ModInfo.xml'
    if (-not (Test-Path $modInfoPath)) { throw "$modlet has no ModInfo.xml" }

    # Well-formedness check - the cheap version of tools/validate.sh
    Get-ChildItem -Path $modlet -Filter *.xml -Recurse | ForEach-Object {
        try { [xml](Get-Content $_.FullName -Raw) | Out-Null }
        catch { throw "XML error in $($_.FullName): $($_.Exception.Message)" }
    }

    [xml]$modInfo = Get-Content $modInfoPath -Raw
    $version = $modInfo.xml.Version.value
    if (-not $version) { throw "Could not read <Version> from $modInfoPath" }

    # Stage without docs so the shipped zip stays lean
    $staging = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString())
    $stagedModlet = Join-Path $staging $modlet
    New-Item -ItemType Directory -Force -Path $stagedModlet | Out-Null
    Copy-Item -Path (Join-Path $modlet '*') -Destination $stagedModlet -Recurse -Force
    Remove-Item -Path (Join-Path $stagedModlet 'docs') -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $stagedModlet 'CHANGELOG.md') -Force -ErrorAction SilentlyContinue
    # Source FBX/maps feed Unity; players only need the built bundle in Resources/
    Remove-Item -Path (Join-Path $stagedModlet 'Resources\src') -Recurse -Force -ErrorAction SilentlyContinue

    $out = Join-Path $dist "$modlet-$version.zip"
    if (Test-Path $out) { Remove-Item $out -Force }
    Compress-Archive -Path $stagedModlet -DestinationPath $out
    Remove-Item -Path $staging -Recurse -Force

    $size = '{0:N0} KB' -f ((Get-Item $out).Length / 1KB)
    Write-Host "built $out ($size)" -ForegroundColor Green
}
