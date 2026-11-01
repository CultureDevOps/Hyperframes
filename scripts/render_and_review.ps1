#requires -Version 5.1
<#
.SYNOPSIS
  One-command local render, soundtrack, MP4 contract and private contact sheet.
.DESCRIPTION
  Local media never leaves this machine. Temporary files inside the public
  source tree are removed, even on failure. No GitHub Actions upload is called.
  npm/HyperFrames may DOWNLOAD dependencies or Chrome on first use.
.EXAMPLE
  .\scripts\render_and_review.ps1 -Composition mvc
.EXAMPLE
  .\scripts\render_and_review.ps1 -Composition intro -PlanOnly
#>
[CmdletBinding()]
param(
    [ValidateSet('intro', 'nounours', 'mvc')]
    [string]$Composition = 'intro',
    [string]$OutputDirectory = (Join-Path $HOME '.hyperframes-private-review'),
    [string]$ExistingMp4 = '',
    [switch]$SkipInstall,
    [switch]$PlanOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$isWindowsHost = ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT)
$comparison = if ($isWindowsHost) { [StringComparison]::OrdinalIgnoreCase } else { [StringComparison]::Ordinal }
$repoPrefix = $repoRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
$outputFull = [IO.Path]::GetFullPath($OutputDirectory)
if ($outputFull.Equals($repoRoot, $comparison) -or $outputFull.StartsWith($repoPrefix, $comparison)) {
    throw 'Private render output MUST be outside this public Git repository.'
}

$profiles = @{
    intro    = @{ Seconds = 10; FileName = 'culturedevops-intro.mp4'; Music = 'generate_soundtrack.py' }
    nounours = @{ Seconds = 10; FileName = 'nounours-antoine-dany.mp4'; Music = 'generate_teddy_soundtrack.py' }
    mvc      = @{ Seconds = 35; FileName = 'mvc-explainer.mp4'; Music = 'generate_mvc_soundtrack.py' }
}
$profile = $profiles[$Composition]
$seconds = [int]$profile.Seconds

if ($PlanOnly) {
    Write-Output "PLAN_ONLY: composition=$Composition seconds=$seconds"
    if ($ExistingMp4) {
        Write-Output 'STEPS: ffprobe contract -> offline contact sheet (existing local MP4)'
    } else {
        Write-Output 'STEPS: npm ci (unless -SkipInstall) -> required HyperFrames lint -> local render -> Python original soundtrack -> FFmpeg AAC mux -> ffprobe contract -> offline contact sheet'
    }
    Write-Output "OUTPUT_OUTSIDE_REPO: $outputFull"
    Write-Output 'MEDIA_UPLOAD: disabled; no publishing or GitHub Actions artifact'
    return
}

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Local command failed (exit $LASTEXITCODE): $Executable"
    }
}

$pythonName = $null
$pythonPrefix = @()
$pythonChoices = if ($isWindowsHost) { @('py', 'python', 'python3') } else { @('python3', 'python') }
foreach ($candidate in $pythonChoices) {
    if (Get-Command -Name $candidate -ErrorAction SilentlyContinue) {
        $pythonName = $candidate
        if ($candidate -eq 'py') { $pythonPrefix = @('-3') }
        break
    }
}
if (-not $pythonName) { throw 'Python 3 not found (py -3 / python3 / python).' }
foreach ($executable in @('ffmpeg', 'ffprobe')) {
    if (-not (Get-Command -Name $executable -ErrorAction SilentlyContinue)) {
        throw "Missing required local executable: $executable"
    }
}
function Invoke-Python {
    param([string[]]$Parameters)
    $all = @($script:pythonPrefix) + @($Parameters)
    Invoke-Checked -Executable $script:pythonName -Arguments $all
}

if ($isWindowsHost) {
    . (Join-Path $PSScriptRoot 'private_output_acl.ps1')
    $outputFull = Initialize-PrivateWindowsDirectory -Path $outputFull
} else {
    $null = New-Item -ItemType Directory -Path $outputFull -Force
    Invoke-Checked -Executable 'chmod' -Arguments @('700', $outputFull)
}
$verifyScript = Join-Path $PSScriptRoot 'verify_render.py'
$reviewScript = Join-Path $PSScriptRoot 'private_visual_review.py'

if ($ExistingMp4) {
    $existing = (Resolve-Path -LiteralPath $ExistingMp4 -ErrorAction Stop).Path
    Invoke-Python -Parameters @($verifyScript, $existing, '--seconds', "$seconds")
    Invoke-Python -Parameters @($reviewScript, $existing, '--seconds', "$seconds", '--out-root', $outputFull)
    Write-Output "REVIEW_ONLY_LOCAL_MP4: $existing"
    return
}

$nodeNpm = if ($isWindowsHost) { 'npm.cmd' } else { 'npm' }
$nodeNpx = if ($isWindowsHost) { 'npx.cmd' } else { 'npx' }
foreach ($exe in @('node', $nodeNpm, $nodeNpx)) {
    if (-not (Get-Command -Name $exe -ErrorAction SilentlyContinue)) {
        throw "Missing required local executable: $exe (install Node.js 22 and npm)"
    }
}
$compositionDir = Join-Path $repoRoot ("compositions/culturedevops/$Composition")
$stageDir = Join-Path $compositionDir 'renders'
$nonce = [Guid]::NewGuid().ToString('N')
$rawName = "ops010-$nonce-raw.mp4"
$rawRel = "renders/$rawName"
$rawFile = Join-Path $stageDir $rawName
$musicFile = Join-Path $stageDir "ops010-$nonce-soundtrack.wav"
$muxed = Join-Path $stageDir "ops010-$nonce-final.mp4"
$final = Join-Path $outputFull "$Composition-$nonce.mp4"
$musicGenerator = Join-Path $PSScriptRoot $profile.Music
$oldUpdateFlag = $env:HYPERFRAMES_NO_UPDATE_CHECK
$env:HYPERFRAMES_NO_UPDATE_CHECK = '1'
try {
    $null = New-Item -ItemType Directory -Path $stageDir -Force
    Push-Location -LiteralPath $repoRoot
    try {
        if (-not $SkipInstall) {
            Invoke-Checked -Executable $nodeNpm -Arguments @('ci', '--no-audit', '--no-fund')
        } elseif (-not (Test-Path (Join-Path $repoRoot 'node_modules/hyperframes'))) {
            throw 'Missing node_modules/hyperframes: run npm ci or omit -SkipInstall.'
        }
    } finally {
        Pop-Location
    }
    Push-Location -LiteralPath $compositionDir
    try {
        Invoke-Checked -Executable $nodeNpx -Arguments @('--no-install', 'hyperframes', 'lint')
        Invoke-Checked -Executable $nodeNpx -Arguments @('--no-install', 'hyperframes', 'render', '--output', $rawRel, '--fps', '30', '--quality', 'high')
    } finally {
        Pop-Location
    }
    if (-not (Test-Path -LiteralPath $rawFile -PathType Leaf)) { throw 'HyperFrames did not create the local raw MP4.' }
    Invoke-Python -Parameters @($musicGenerator, $musicFile)
    Invoke-Checked -Executable 'ffmpeg' -Arguments @(
        '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
        '-i', $rawFile, '-i', $musicFile,
        '-map', '0:v:0', '-map', '1:a:0',
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        '-t', "$seconds", '-movflags', '+faststart', $muxed
    )
    if (-not (Test-Path -LiteralPath $muxed -PathType Leaf)) { throw 'FFmpeg did not create the muxed MP4.' }
    if ($isWindowsHost) {
        # Stage inside private NTFS, verify hash + ACL and atomically rename.
        # No existing final or partial copy may survive a failed publish attempt.
        $null = Copy-PrivateWindowsMedia -Source $muxed -Destination $final
    } else {
        Move-Item -LiteralPath $muxed -Destination $final -ErrorAction Stop
    }
    Invoke-Python -Parameters @($verifyScript, $final, '--seconds', "$seconds")
    Invoke-Python -Parameters @($reviewScript, $final, '--seconds', "$seconds", '--out-root', $outputFull)
    Write-Output "LOCAL_VIDEO: $final"
    Write-Output 'Review the local MP4 for timing, motion and audio; the contact sheet alone is not a visual sign-off.'
} finally {
    foreach ($temporary in @($rawFile, $musicFile, $muxed)) {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        }
    }
    if ($null -eq $oldUpdateFlag) {
        Remove-Item -Path Env:HYPERFRAMES_NO_UPDATE_CHECK -ErrorAction SilentlyContinue
    } else {
        $env:HYPERFRAMES_NO_UPDATE_CHECK = $oldUpdateFlag
    }
}
