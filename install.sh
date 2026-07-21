#!/usr/bin/env bash
# jeemookit: global Skills + AGENT.md + project scripts
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(pwd)"
USER_SKILLS="${HOME}/.cursor/skills"
FORCE_AGENT=false
SKIP_DEPS=false
SKILLS_ONLY=false
AGENT_ONLY=false
SKIP_PPT_MASTER=false

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Options:
  --project-root PATH   Target project directory (default: current directory)
  --force-agent         Overwrite existing AGENT.md
  --skip-deps           Skip pip/npm install
  --skills-only         Install skills only
  --agent-only          Install AGENT.md and project scripts only
  --skip-ppt-master     Skip deploying the incoa PPT Master deck template
  -h, --help            Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root) PROJECT_ROOT="$2"; shift 2 ;;
    --force-agent) FORCE_AGENT=true; shift ;;
    --skip-deps) SKIP_DEPS=true; shift ;;
    --skills-only) SKILLS_ONLY=true; shift ;;
    --agent-only) AGENT_ONLY=true; shift ;;
    --skip-ppt-master) SKIP_PPT_MASTER=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

step() { echo ">> $1"; }

if [[ ! -f "$KIT_ROOT/manifest.json" ]]; then
  echo "manifest.json not found in $KIT_ROOT" >&2
  exit 1
fi

mkdir -p "$PROJECT_ROOT"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

install_skills() {
  step "Installing skills to $USER_SKILLS"
  mkdir -p "$USER_SKILLS"

  python3 - <<'PY' "$KIT_ROOT" "$USER_SKILLS"
import json, shutil, sys
from pathlib import Path

kit, user_skills = Path(sys.argv[1]), Path(sys.argv[2])
manifest = json.loads((kit / "manifest.json").read_text(encoding="utf-8"))

for skill in manifest["skills"]:
    src = kit / skill["path"]
    dest = user_skills / skill["id"]
    if not src.is_dir():
        print(f"  skip missing: {skill['id']}")
        continue
    print(f"  - {skill['id']} v{skill['version']}")
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
PY

  if [[ "$SKIP_DEPS" == true ]]; then
    echo "  skipped deps (--skip-deps)"
    return
  fi

  step "Installing pip/npm dependencies"

  python3 - <<'PY' "$KIT_ROOT" "$USER_SKILLS"
import json, subprocess, sys
from pathlib import Path

kit, user_skills = Path(sys.argv[1]), Path(sys.argv[2])
manifest = json.loads((kit / "manifest.json").read_text(encoding="utf-8"))

for skill in manifest["skills"]:
    dest = user_skills / skill["id"]
    inst = skill.get("install", {})
    if inst.get("pip"):
        req = dest / inst["pip"]
        if req.is_file():
            print(f"  pip: {skill['id']}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req), "-q"])
    if inst.get("npm") and (dest / "package.json").is_file():
        print(f"  npm: {skill['id']} (first run ~340MB)")
        subprocess.check_call(["npm", "install", "--no-fund", "--no-audit"], cwd=dest)
PY
}

deploy_ppt_templates() {
  step "Deploying PPT Master deck templates"

  python3 - <<'PY' "$KIT_ROOT" "$HOME"
import json, shutil, subprocess, sys
from pathlib import Path

kit, home = Path(sys.argv[1]), Path(sys.argv[2])
manifest = json.loads((kit / "manifest.json").read_text(encoding="utf-8"))
cfg = manifest.get("pptMaster")
if not cfg:
    sys.exit(0)

def find_root():
    for rel in cfg.get("installCandidates", []):
        base = home / rel
        if (base / "scripts" / "register_template.py").is_file() and (base / "templates").is_dir():
            return base
    return None

root = find_root()
if root is None:
    repo = cfg.get("repo", "https://github.com/hugohe3/ppt-master")
    print("\n  未检测到 PPT Master skill，已跳过 incoa 模板部署。")
    print("  请先从 GitHub 页面下载安装 PPT Master，然后重新运行本安装脚本：")
    print(f"    页面: {repo}")
    print("    方式A (skill 包, 需 Node/npx):  npx -y skills add hugohe3/ppt-master")
    print("    方式B (完整仓库, 需 git):        git clone https://github.com/hugohe3/ppt-master.git")
    print("  安装完成后再次执行: ./install.sh  (会自动部署并注册 incoa 模板)\n")
    sys.exit(0)

print(f"  ppt-master: {root}")
decks_dir = root / "templates" / "decks"
decks_dir.mkdir(parents=True, exist_ok=True)

for deck in cfg.get("decks", []):
    src = kit / deck["path"]
    dest = decks_dir / deck["id"]
    if not src.is_dir():
        print(f"  skip missing deck source: {deck['id']} ({src})")
        continue
    print(f"  - deck: {deck['id']}")
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    try:
        subprocess.check_call(
            [sys.executable, "scripts/register_template.py", deck["id"], "--kind", "deck"],
            cwd=str(root),
        )
    except Exception as e:
        print(f"  register_template failed for {deck['id']}: {e}")
PY
}

install_agent() {
  local template="$KIT_ROOT/templates/AGENT.md"
  local target="$PROJECT_ROOT/AGENT.md"

  if [[ -f "$KIT_ROOT/manifest.json" ]]; then
    local rel
    rel="$(python3 -c "import json; m=json.load(open('$KIT_ROOT/manifest.json')); print(m.get('templates',{}).get('agent','templates/AGENT.md'))")"
    template="$KIT_ROOT/$rel"
  fi

  step "Installing AGENT.md to $target"

  if [[ ! -f "$template" ]]; then
    echo "Template not found: $template" >&2
    exit 1
  fi

  if [[ -f "$target" && "$FORCE_AGENT" != true ]]; then
    echo "  AGENT.md exists, skipped (use --force-agent to overwrite)"
    return
  fi

  cp "$template" "$target"
  echo "  wrote AGENT.md"
}

install_project_scripts() {
  local template_dir="$KIT_ROOT/templates/scripts"
  local target_dir="$PROJECT_ROOT/scripts"

  [[ -d "$template_dir" ]] || return

  step "Installing project scripts to $target_dir"
  mkdir -p "$target_dir"

  for file in "$template_dir"/*; do
    [[ -f "$file" ]] || continue
    local name
    name="$(basename "$file")"
    local target_file="$target_dir/$name"

    if [[ -f "$target_file" ]]; then
      echo "  $name exists, skipped"
      continue
    fi

    cp "$file" "$target_file"
    chmod +x "$target_file" 2>/dev/null || true
    echo "  wrote $target_file"
  done
}

if [[ "$AGENT_ONLY" != true ]]; then
  install_skills
  if [[ "$SKIP_PPT_MASTER" == true ]]; then
    echo "  skipped PPT Master template deploy (--skip-ppt-master)"
  else
    deploy_ppt_templates
  fi
fi

if [[ "$SKILLS_ONLY" != true ]]; then
  install_agent
  install_project_scripts
fi

echo
echo "Done."
echo "  Global skills:  $USER_SKILLS"
if [[ "$SKILLS_ONLY" != true ]]; then
  echo "  Project AGENT.md: $PROJECT_ROOT/AGENT.md"
  echo "  Project scripts:  $PROJECT_ROOT/scripts"
fi
echo
echo "Next steps:"
echo "  1. 编辑 AGENT.md"
echo "  2. Restart or open a new Cursor Agent chat"
