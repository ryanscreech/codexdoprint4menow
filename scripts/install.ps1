[CmdletBinding(SupportsShouldProcess = $true)]
param([switch]$LegacyPrompts, [string]$ProjectPath)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Install-Directory([string]$Source,[string]$Destination) {
  if (!(Test-Path $Source)) { throw "Missing source: $Source" }
  if ($PSCmdlet.ShouldProcess($Destination,"Install from $Source")) {
    New-Item -ItemType Directory -Force -Path (Split-Path $Destination) | Out-Null
    if (Test-Path $Destination) {
      $backup = "$Destination.backup.$(Get-Date -Format yyyyMMdd-HHmmss)"
      Move-Item -LiteralPath $Destination -Destination $backup
      Write-Host "Backed up to $backup"
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse
    Write-Host "Installed $Destination"
  }
}

function Install-File([string]$Source,[string]$Destination) {
  if ($PSCmdlet.ShouldProcess($Destination,"Install from $Source")) {
    New-Item -ItemType Directory -Force -Path (Split-Path $Destination) | Out-Null
    if (Test-Path $Destination) {
      $backup = "$Destination.backup.$(Get-Date -Format yyyyMMdd-HHmmss)"
      Copy-Item -LiteralPath $Destination -Destination $backup
      Write-Host "Backed up to $backup"
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    Write-Host "Installed $Destination"
  }
}

Install-Directory (Join-Path $repo 'skills\cad-continuity') (Join-Path $HOME '.agents\skills\cad-continuity')
if ($LegacyPrompts) {
  $codex = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
  foreach ($cmd in @('ingest','audit')) {
    Install-File (Join-Path $repo "prompts\$cmd.md") (Join-Path $codex "prompts\$cmd.md")
  }
}
if ($ProjectPath) {
  if (!(Test-Path $ProjectPath -PathType Container)) { throw "Project not found: $ProjectPath" }
  $kb = Join-Path $ProjectPath 'cad-knowledge'
  if (Test-Path $kb) {
    Write-Host "Preserving existing knowledge base: $kb"
  } else {
    Install-Directory (Join-Path $repo 'templates\project-knowledge') $kb
  }
  Write-Host 'Merge templates\AGENTS.project.example.md into project AGENTS.md manually.'
}
Write-Host 'Restart Codex. Test $cad-continuity; legacy slash prompts need a compatible client.'
