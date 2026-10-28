# Installs the GoharyAI skills into ~/.claude/skills and checks the environment (Windows PowerShell).
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$dest = if ($env:CLAUDE_SKILLS_DIR) { $env:CLAUDE_SKILLS_DIR } else { Join-Path $HOME ".claude\skills" }
New-Item -ItemType Directory -Force $dest | Out-Null
Get-ChildItem (Join-Path $here "skills") -Directory -Filter "goharyai-*" | ForEach-Object {
  $target = Join-Path $dest $_.Name
  if (Test-Path $target) { Remove-Item -Recurse -Force $target }
  Copy-Item -Recurse $_.FullName $target
  Write-Host "installed $($_.Name)"
}
Push-Location (Join-Path $dest "goharyai-core")
npm install --no-audit --no-fund --silent
Pop-Location
node (Join-Path $dest "goharyai-core\scripts\run.js") env.py
Write-Host ""
Write-Host "Done. In Claude Code, try: /goharyai-reel  (or just describe the video you want)."
