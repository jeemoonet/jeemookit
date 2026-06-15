#!/usr/bin/env bash
# jeemookit: global Skills + AGENT.md + 项目配置
set -euo pipefail

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(pwd)"
USER_SKILLS="${HOME}/.cursor/skills"
FORCE_AGENT=false
FORCE_PROJECT=false
SKIP_DEPS=false
SKILLS_ONLY=false
AGENT_ONLY=false

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Options:
  --project-root PATH   Target project directory (default: current directory)
  --force-agent         Overwrite existing AGENT.md
  --force-project       Overwrite .jeemoo/project.json
  --skip-deps           Skip pip/npm install
  --skills-only         Install skills only
  --agent-only          Install AGENT.md and project config only
  -h, --help            Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root) PROJECT_ROOT="$2"; shift 2 ;;
    --force-agent) FORCE_AGENT=true; shift ;;
    --force-project) FORCE_PROJECT=true; shift ;;
    --skip-deps) SKIP_DEPS=true; shift ;;
    --skills-only) SKILLS_ONLY=true; shift ;;
    --agent-only) AGENT_ONLY=true; shift ;;
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

install_project_jeemoo() {
  local template_dir="$KIT_ROOT/templates/.jeemoo"
  local target_dir="$PROJECT_ROOT/.jeemoo"
  local target_config="$target_dir/project.json"

  [[ -d "$template_dir" ]] || return

  step "Installing project config to $target_dir"
  mkdir -p "$target_dir"

  if [[ -f "$target_config" && "$FORCE_PROJECT" != true ]]; then
    echo "  .jeemoo/project.json exists, skipped (use --force-project)"
  else
    local name
    name="$(basename "$PROJECT_ROOT")"
    sed "s/YOUR_PROJECT_NAME/$name/g" "$template_dir/project.json" > "$target_config"
    echo "  .jeemoo/project.json written"
  fi

  cp "$template_dir/.gitignore" "$target_dir/.gitignore"
}

if [[ "$AGENT_ONLY" != true ]]; then
  install_skills
fi

if [[ "$SKILLS_ONLY" != true ]]; then
  install_agent
fi

if [[ "$SKILLS_ONLY" != true ]]; then
  install_project_jeemoo
fi

echo
echo "Done."
echo "  Global skills:  $USER_SKILLS"
if [[ "$SKILLS_ONLY" != true ]]; then
  echo "  Project AGENT.md: $PROJECT_ROOT/AGENT.md"
  echo "  Project config:   $PROJECT_ROOT/.jeemoo/project.json"
fi
echo
echo "Next steps:"
echo "  1. 编辑 AGENT.md 与 .jeemoo/project.json"
echo "  2. Restart or open a new Cursor Agent chat"
