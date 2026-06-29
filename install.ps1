#Requires -Version 5.1
param(
    [string] $ProjectRoot = (Get-Location).Path,
    [switch] $ForceAgent,
    [switch] $ForceProject,
    [switch] $SkipDeps,
    [switch] $SkillsOnly,
    [switch] $AgentOnly
)

$ErrorActionPreference = 'Stop'

$KitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$UserSkills = Join-Path $env:USERPROFILE '.cursor\skills'
$ManifestPath = Join-Path $KitRoot 'manifest.json'

function Write-Step([string]$Message) {
    Write-Host ">> $Message" -ForegroundColor Cyan
}

function Test-CommandExists([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-ProjectJeemoo {
    param([string]$Root)

    $templateDir = Join-Path $KitRoot 'templates\.jeemoo'
    $targetDir = Join-Path $Root '.jeemoo'
    $targetConfig = Join-Path $targetDir 'project.json'

    if (-not (Test-Path $templateDir)) { return }

    Write-Step "Install project config to $targetDir"
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

    if ((Test-Path $targetConfig) -and -not $ForceProject) {
        Write-Host '  .jeemoo/project.json exists, skipped (use -ForceProject)' -ForegroundColor Yellow
    } else {
        $content = Get-Content (Join-Path $templateDir 'project.json') -Raw -Encoding UTF8
        $projectName = Split-Path $Root -Leaf
        $content = $content -replace 'YOUR_PROJECT_NAME', $projectName
        $content | Set-Content $targetConfig -Encoding UTF8
        Write-Host '  .jeemoo/project.json written' -ForegroundColor Green
    }

    $gitignoreSrc = Join-Path $templateDir '.gitignore'
    $gitignoreDst = Join-Path $targetDir '.gitignore'
    if (Test-Path $gitignoreSrc) {
        Copy-Item $gitignoreSrc $gitignoreDst -Force
    }
}

function Install-ProjectScripts {
    param([string]$Root)

    $templateDir = Join-Path $KitRoot 'templates\scripts'
    $targetDir = Join-Path $Root 'scripts'

    if (-not (Test-Path $templateDir)) { return }

    Write-Step "Install project scripts to $targetDir"
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

    Get-ChildItem -Path $templateDir -File | ForEach-Object {
        $targetFile = Join-Path $targetDir $_.Name
        if (Test-Path $targetFile) {
            Write-Host "  $($_.Name) exists, skipped" -ForegroundColor Yellow
            return
        }

        Copy-Item $_.FullName $targetFile -Force
        Write-Host "  wrote $targetFile" -ForegroundColor Green
    }
}

if (-not (Test-Path $ManifestPath)) {
    throw 'manifest.json not found. Run install.ps1 from jeemookit directory.'
}

$projectPath = $ProjectRoot
if (-not (Test-Path $projectPath)) {
    New-Item -ItemType Directory -Force -Path $projectPath | Out-Null
}
$ProjectRoot = (Resolve-Path -LiteralPath $projectPath).Path

$manifest = Get-Content $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

if (-not $AgentOnly) {
    Write-Step "Install skills to $UserSkills"
    New-Item -ItemType Directory -Force -Path $UserSkills | Out-Null

    foreach ($skill in $manifest.skills) {
        $src = Join-Path $KitRoot $skill.path
        $dest = Join-Path $UserSkills $skill.id

        if (-not (Test-Path $src)) {
            Write-Warning "Skip missing skill: $($skill.id)"
            continue
        }

        Write-Host "  - $($skill.id) v$($skill.version)"
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        Copy-Item -Path (Join-Path $src '*') -Destination $dest -Recurse -Force
    }

    if (-not $SkipDeps) {
        Write-Step 'Install skill dependencies (pip / npm)'

        if (-not (Test-CommandExists 'python')) {
            Write-Warning 'python not found, skip pip'
        }
        if (-not (Test-CommandExists 'npm')) {
            Write-Warning 'npm not found, skip npm (md-to-word needs Node.js)'
        }

        foreach ($skill in $manifest.skills) {
            $dest = Join-Path $UserSkills $skill.id
            if (-not (Test-Path $dest)) { continue }

            $pipFile = $skill.install.pip
            if ($pipFile -and (Test-CommandExists 'python')) {
                $req = Join-Path $dest $pipFile
                if (Test-Path $req) {
                    Write-Host "  pip: $($skill.id)"
                    & python -m pip install -r $req --quiet
                }
            }

            if ($skill.install.npm -and (Test-CommandExists 'npm')) {
                $pkg = Join-Path $dest 'package.json'
                if (Test-Path $pkg) {
                    Write-Host "  npm: $($skill.id) (~340MB first time)"
                    Push-Location $dest
                    try {
                        & npm install --no-fund --no-audit
                    } finally {
                        Pop-Location
                    }
                }
            }
        }
    } else {
        Write-Host '  Skipped dependencies (-SkipDeps)' -ForegroundColor Yellow
    }
}

if (-not $SkillsOnly) {
    $templateRel = if ($manifest.templates.agent) { $manifest.templates.agent } else { 'templates/AGENT.md' }
    $template = Join-Path $KitRoot ($templateRel -replace '/', '\')
    $target = Join-Path $ProjectRoot 'AGENT.md'

    if (-not (Test-Path $template)) {
        throw "Template not found: $template"
    }

    Write-Step "Install AGENT.md to $target"

    if ((Test-Path $target) -and -not $ForceAgent) {
        Write-Host '  AGENT.md exists, skipped (use -ForceAgent)' -ForegroundColor Yellow
    } else {
        Copy-Item $template $target -Force
        Write-Host '  AGENT.md written' -ForegroundColor Green
    }
}

if (-not $SkillsOnly) {
    Install-ProjectJeemoo -Root $ProjectRoot
    Install-ProjectScripts -Root $ProjectRoot
}

Write-Host ''
Write-Host 'Done.' -ForegroundColor Green
Write-Host "  Global skills:  $UserSkills"
if (-not $SkillsOnly) {
    Write-Host "  Project AGENT.md: $(Join-Path $ProjectRoot 'AGENT.md')"
    Write-Host "  Project config:   $(Join-Path $ProjectRoot '.jeemoo\project.json')"
    Write-Host "  Project scripts:  $(Join-Path $ProjectRoot 'scripts')"
}
Write-Host ''
Write-Host 'Next steps:'
Write-Host '  1. 编辑 AGENT.md 与 .jeemoo/project.json'
Write-Host '  2. Restart or open a new Cursor Agent chat'
