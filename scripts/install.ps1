#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [switch]$LegacyPrompts,
  [string]$ProjectPath,
  [switch]$ProjectLocal,
  [switch]$Force,
  [string]$UserRoot = $HOME
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

function Assert-PlainPath([string]$Path) {
  # Refuse symlinks/junctions rather than updating a different installation.
  $cursor = [IO.Path]::GetFullPath($Path)
  while ($cursor) {
    if (Test-Path -LiteralPath $cursor) {
      $item = Get-Item -LiteralPath $cursor -Force
      if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Linked install path is not supported: $cursor"
      }
    }
    $cursor = Split-Path -Parent $cursor
  }
}

function Get-Inventory([string]$Path) {
  $item = Get-Item -LiteralPath $Path -Force
  if (!$item.PSIsContainer) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }
  $base = $item.FullName.TrimEnd([IO.Path]::DirectorySeparatorChar)
  $entries = @(Get-ChildItem -LiteralPath $Path -Recurse -Force | Sort-Object FullName | ForEach-Object {
    if ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked content is not supported: $($_.FullName)" }
    $relative = $_.FullName.Substring($base.Length)
    if ($_.PSIsContainer) { "D $relative" }
    else { "F $relative $((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)" }
  })
  return ($entries -join "`n")
}

# Validate the entire plan before creating directories or moving existing files.
if ($ProjectLocal -and !$ProjectPath) { throw '-ProjectLocal requires -ProjectPath.' }
if ($ProjectPath) {
  if (!(Test-Path -LiteralPath $ProjectPath -PathType Container)) { throw "Project not found: $ProjectPath" }
  $ProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
}
$scopeRoot = if ($ProjectLocal) { $ProjectPath } else { [IO.Path]::GetFullPath($UserRoot) }
$backupRoot = Join-Path $scopeRoot '.cad-continuity-backups'
Assert-PlainPath $backupRoot
$plan = @(@{ Source = Join-Path $repo 'skills/cad-continuity'; Destination = Join-Path $scopeRoot '.agents/skills/cad-continuity' })
if ($LegacyPrompts) {
  $codex = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $UserRoot '.codex' }
  foreach ($cmd in @('ingest', 'audit')) {
    $plan += @{ Source = Join-Path $repo "prompts/$cmd.md"; Destination = Join-Path $codex "prompts/$cmd.md" }
  }
}
if ($ProjectPath) {
  $kb = Join-Path $ProjectPath 'cad-knowledge'
  Assert-PlainPath $kb
  if (Test-Path -LiteralPath $kb) {
    if (!(Test-Path -LiteralPath $kb -PathType Container)) { throw "Knowledge path is not a directory: $kb" }
    Write-Host "Preserving existing knowledge base: $kb"
  } else {
    $plan += @{ Source = Join-Path $repo 'templates/project-knowledge'; Destination = $kb }
  }
}
$pending = @()
foreach ($entry in $plan) {
  $source = $entry.Source
  $destination = $entry.Destination
  if (!(Test-Path -LiteralPath $source)) { throw "Missing source: $source" }
  Assert-PlainPath $source
  Assert-PlainPath $destination
  $sourceInventory = Get-Inventory $source
  if (Test-Path -LiteralPath $destination) {
    if ((Get-Item -LiteralPath $source).PSIsContainer -ne (Get-Item -LiteralPath $destination).PSIsContainer) {
      throw "Destination has the wrong file type: $destination"
    }
    if ($sourceInventory -ceq (Get-Inventory $destination)) {
      Write-Host "Already current: $destination"
      continue
    }
    if (!$Force -and !$WhatIfPreference) {
      throw "Existing content differs: $destination. Review it, then use -Force to replace it with a backup."
    }
  }
  $pending += $entry
}

foreach ($entry in $pending) {
  $source = $entry.Source
  $destination = $entry.Destination
  if (!$PSCmdlet.ShouldProcess($destination, "Install from $source (back up existing content outside skill discovery)")) { continue }
  $transaction = Join-Path $backupRoot ([guid]::NewGuid().ToString('N'))
  $staged = Join-Path $transaction 'staged'
  $previous = Join-Path $transaction 'previous'
  $failed = Join-Path $transaction 'failed'
  [IO.Directory]::CreateDirectory($transaction) | Out-Null
  $movedOld = $false
  try {
    Copy-Item -LiteralPath $source -Destination $staged -Recurse
    if ((Get-Inventory $source) -cne (Get-Inventory $staged)) { throw "Staged copy failed verification: $source" }
    [IO.Directory]::CreateDirectory((Split-Path -Parent $destination)) | Out-Null
    if (Test-Path -LiteralPath $destination) {
      Move-Item -LiteralPath $destination -Destination $previous
      $movedOld = $true
      Write-Host "Backup for ${destination}: $previous"
    }
    Move-Item -LiteralPath $staged -Destination $destination
    Write-Host "Installed $destination"
  } catch {
    if ($movedOld) {
      if (Test-Path -LiteralPath $destination) {
        Move-Item -LiteralPath $destination -Destination $failed
        Write-Warning "Partial activation retained at $failed"
      }
      Move-Item -LiteralPath $previous -Destination $destination
    }
    throw
  } finally {
    if (Test-Path -LiteralPath $staged) { Remove-Item -LiteralPath $staged -Recurse -Force }
    if (!(Test-Path -LiteralPath $previous) -and !(Test-Path -LiteralPath $failed)) {
      Remove-Item -LiteralPath $transaction -Recurse -Force
    }
  }
}
if ($ProjectPath) { Write-Host 'Merge templates/AGENTS.project.example.md into project AGENTS.md manually.' }
if ($WhatIfPreference) { Write-Host 'Preview only: no installation performed.' }
else { Write-Host 'Files ready. Verify skill discovery in Codex; restart if needed. Legacy prompts require a compatible client.' }
