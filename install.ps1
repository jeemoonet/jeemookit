#Requires -Version 5.1
param(
    [string] $ProjectRoot = (Get-Location).Path,
    [switch] $ForceAgent,
    [switch] $SkipDeps,
    [switch] $SkillsOnly,
    [switch] $AgentOnly,
    [switch] $SkipPptMaster
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

function Find-PptMasterRoot {
    param([string[]]$Candidates)

    foreach ($rel in $Candidates) {
        $base = Join-Path $env:USERPROFILE $rel
        if ((Test-Path (Join-Path $base 'scripts\register_template.py')) -and (Test-Path (Join-Path $base 'templates'))) {
            return $base
        }
    }
    return $null
}

function Show-PptMasterInstallHint {
    param([string]$Repo)

    Write-Host ''
    Write-Host '  未检测到 PPT Master skill，已跳过 incoa 模板部署。' -ForegroundColor Yellow
    Write-Host '  请先从 GitHub 页面下载安装 PPT Master，然后重新运行本安装脚本：' -ForegroundColor Yellow
    Write-Host "    页面: $Repo" -ForegroundColor Cyan
    Write-Host '    方式A (skill 包, 需 Node/npx):  npx -y skills add hugohe3/ppt-master' -ForegroundColor Cyan
    Write-Host '    方式B (完整仓库, 需 git):        git clone https://github.com/hugohe3/ppt-master.git' -ForegroundColor Cyan
    Write-Host '  安装完成后再次执行: .\install.ps1  (会自动部署并注册 incoa 模板)' -ForegroundColor Yellow
    Write-Host ''
}

function Deploy-PptTemplates {
    if (-not $manifest.pptMaster) { return }
    $cfg = $manifest.pptMaster

    Write-Step 'Deploy PPT Master deck templates'

    $pptRoot = Find-PptMasterRoot -Candidates $cfg.installCandidates
    if (-not $pptRoot) {
        Show-PptMasterInstallHint -Repo $cfg.repo
        return
    }
    Write-Host "  ppt-master: $pptRoot" -ForegroundColor Green

    $decksDir = Join-Path $pptRoot 'templates\decks'
    New-Item -ItemType Directory -Force -Path $decksDir | Out-Null

    foreach ($deck in $cfg.decks) {
        $srcDeck = Join-Path $KitRoot ($deck.path -replace '/', '\')
        $destDeck = Join-Path $decksDir $deck.id

        if (-not (Test-Path $srcDeck)) {
            Write-Warning "  Skip missing deck source: $($deck.id) ($srcDeck)"
            continue
        }

        Write-Host "  - deck: $($deck.id)"
        New-Item -ItemType Directory -Force -Path $destDeck | Out-Null
        Copy-Item -Path (Join-Path $srcDeck '*') -Destination $destDeck -Recurse -Force

        if (Test-CommandExists 'python') {
            Push-Location $pptRoot
            try {
                $env:PYTHONUTF8 = '1'
                & python 'scripts/register_template.py' $deck.id '--kind' 'deck'
            } catch {
                Write-Warning "  register_template failed for $($deck.id): $($_.Exception.Message)"
            } finally {
                Pop-Location
            }
        } else {
            Write-Warning "  python not found; copied deck but did not register $($deck.id)"
        }
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

if (-not $AgentOnly) {
    if ($SkipPptMaster) {
        Write-Host '  Skipped PPT Master template deploy (-SkipPptMaster)' -ForegroundColor Yellow
    } else {
        Deploy-PptTemplates
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
    Install-ProjectScripts -Root $ProjectRoot
}

Write-Host ''
Write-Host 'Done.' -ForegroundColor Green
Write-Host "  Global skills:  $UserSkills"
if (-not $SkillsOnly) {
    Write-Host "  Project AGENT.md: $(Join-Path $ProjectRoot 'AGENT.md')"
    Write-Host "  Project scripts:  $(Join-Path $ProjectRoot 'scripts')"
}
Write-Host ''
Write-Host 'Next steps:'
Write-Host '  1. 编辑 AGENT.md'
Write-Host '  2. Restart or open a new Cursor Agent chat'
