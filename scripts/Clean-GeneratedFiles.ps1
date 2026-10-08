[CmdletBinding(SupportsShouldProcess)]
param()
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Split-Path $PSScriptRoot -Parent)).Path.TrimEnd('\')
# Explicit historical directories only. Current build cache, final artifacts,
# TLS, account configuration, SDK archive and real database backups are preserved.
$relativePaths = @(
    '.local\console-deps', '.local\captures', '.local\diagnostics',
    '.local\research', '.local\upstream', '.local\visual',
    '.local\ui-install-preview', '.local\release-smoke-20261007',
    '.local\__pycache__', '.local\backups\ps5-final-rollout-20261008',
    'artifacts\releases', 'artifacts\sdk-smoke',
    'artifacts\console\final-ui\TrophySync-PS5-UI-candidate.zip',
    'artifacts\console\final-ui\PPSA99889\licenses\stb_easy_font.txt',
    'console\tests\__pycache__', 'web\test-results', 'web\playwright-report'
)
$consoleArtifacts = Join-Path $root 'artifacts\console'
if (Test-Path -LiteralPath $consoleArtifacts -PathType Container) {
    foreach ($item in Get-ChildItem -LiteralPath $consoleArtifacts -Force) {
        if ($item.Name -ne 'final-ui') { $relativePaths += 'artifacts\console\' + $item.Name }
    }
}
$targets = @()
foreach ($relative in $relativePaths) {
    $target = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $target.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing target outside workspace: $target"
    }
    if (-not (Test-Path -LiteralPath $target)) { continue }
    $resolved = (Resolve-Path -LiteralPath $target).Path
    if (-not $resolved.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing resolved target outside workspace: $resolved"
    }
    $item = Get-Item -LiteralPath $resolved -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Refusing reparse point: $resolved" }
    if ($item.PSIsContainer) {
        $links = @(Get-ChildItem -LiteralPath $resolved -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
        if ($links.Count) {
            Write-Warning "Skipped historical cache with Linux reparse points: $resolved. Remove it manually if desired; it is ignored and unused."
            continue
        }
    }
    $targets += $resolved
}
foreach ($target in $targets) {
    if ($PSCmdlet.ShouldProcess($target, 'Delete historical generated files')) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
Write-Host "Reviewed $($targets.Count) historical targets; current application/data preserved."
