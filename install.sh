#!/usr/bin/env bash
#
# Install the solo-orchestrator skill into your agents' skill directories.
#
#   ./install.sh                      # symlink for Claude Code + Codex/Cursor (user-level)
#   ./install.sh --targets all        # add OpenCode and Cursor's native path
#   ./install.sh --copy               # vendor a copy instead of symlinking
#   ./install.sh --project            # install into ./.claude, ./.agents, ... instead of $HOME
#   ./install.sh --uninstall          # remove what this script installed
#   ./install.sh --list               # show where the skill is currently installed
#
set -euo pipefail

SKILL_NAME="solo-orchestrator"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="link"        # link | copy
SCOPE="user"       # user | project
ACTION="install"   # install | uninstall | list
FORCE=0
TARGETS=""

usage() {
  sed -n '2,11p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  cat <<'EOF'

Targets:
  claude     Claude Code            ~/.claude/skills        (or ./.claude/skills)
  codex      Codex CLI + Cursor     ~/.agents/skills        (or ./.agents/skills)
  cursor     Cursor native path     ~/.cursor/skills        (or ./.cursor/skills)
  opencode   OpenCode               ~/.config/opencode/skills   (user scope only)

Default targets: claude,codex

Codex and Cursor both read the `.agents/skills` path, so the default covers all
three of Claude Code, Codex, and Cursor. Kimi Code has no fixed skills
directory -- launch it with `--skills-dir` instead (see README).

Options:
  --targets <list>   Comma-separated target list, or "all"
  --copy             Copy the skill instead of symlinking (no `git pull` updates)
  --project          Install into the current directory instead of $HOME
  --uninstall        Remove installed entries for the selected targets
  --list             Report where the skill is installed and exit
  --force            Allow uninstall to remove a real directory (copy installs)
  -h, --help         Show this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --targets)   TARGETS="${2:?--targets needs a value}"; shift 2 ;;
    --targets=*) TARGETS="${1#*=}"; shift ;;
    --copy)      MODE="copy"; shift ;;
    --link)      MODE="link"; shift ;;
    --project)   SCOPE="project"; shift ;;
    --uninstall) ACTION="uninstall"; shift ;;
    --list)      ACTION="list"; shift ;;
    --force)     FORCE=1; shift ;;
    -h|--help)   usage; exit 0 ;;
    *) echo "error: unknown option '$1'" >&2; usage >&2; exit 2 ;;
  esac
done

[ -n "$TARGETS" ] || TARGETS="claude,codex"
[ "$TARGETS" = "all" ] && TARGETS="claude,codex,cursor,opencode"
[ "$ACTION" = "list" ] && TARGETS="claude,codex,cursor,opencode"

# Sanity: refuse to install something that isn't this skill.
if [ ! -f "$SRC/SKILL.md" ]; then
  echo "error: no SKILL.md next to install.sh ($SRC) -- run this from the repo." >&2
  exit 1
fi

skills_dir_for() {
  case "$1" in
    claude)   [ "$SCOPE" = user ] && echo "$HOME/.claude/skills" || echo "$PWD/.claude/skills" ;;
    codex)    [ "$SCOPE" = user ] && echo "$HOME/.agents/skills" || echo "$PWD/.agents/skills" ;;
    cursor)   [ "$SCOPE" = user ] && echo "$HOME/.cursor/skills" || echo "$PWD/.cursor/skills" ;;
    opencode) [ "$SCOPE" = user ] && echo "$HOME/.config/opencode/skills" || echo "" ;;
    *)        echo "" ;;
  esac
}

label_for() {
  case "$1" in
    claude)   echo "Claude Code" ;;
    codex)    echo "Codex CLI (+ Cursor)" ;;
    cursor)   echo "Cursor (native path)" ;;
    opencode) echo "OpenCode" ;;
  esac
}

installed=0
skipped=0

for target in ${TARGETS//,/ }; do
  dir="$(skills_dir_for "$target")"
  label="$(label_for "$target")"

  if [ -z "$dir" ]; then
    case "$target" in
      opencode) echo "skip  OpenCode -- no project-scope skills path; use user scope" ;;
      *)        echo "error: unknown target '$target'" >&2; exit 2 ;;
    esac
    skipped=$((skipped + 1))
    continue
  fi

  dest="$dir/$SKILL_NAME"

  case "$ACTION" in
    list)
      if [ -L "$dest" ]; then
        echo "link  $label  $dest -> $(readlink "$dest")"
      elif [ -d "$dest" ]; then
        echo "copy  $label  $dest"
      else
        echo "  --  $label  not installed"
      fi
      ;;

    uninstall)
      if [ -L "$dest" ]; then
        rm "$dest"
        echo "removed  $label  $dest"
        installed=$((installed + 1))
      elif [ -d "$dest" ]; then
        if [ "$FORCE" = 1 ]; then
          rm -rf "$dest"
          echo "removed  $label  $dest (copy)"
          installed=$((installed + 1))
        else
          echo "skip     $label  $dest is a real directory -- rerun with --force to delete it"
          skipped=$((skipped + 1))
        fi
      else
        echo "skip     $label  nothing installed at $dest"
        skipped=$((skipped + 1))
      fi
      ;;

    install)
      mkdir -p "$dir"

      # Already pointing at this checkout? Nothing to do.
      if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$SRC" ]; then
        echo "ok       $label  already linked -> $SRC"
        installed=$((installed + 1))
        continue
      fi

      if [ -e "$dest" ] || [ -L "$dest" ]; then
        echo "skip     $label  $dest already exists -- remove it first (./install.sh --uninstall)"
        skipped=$((skipped + 1))
        continue
      fi

      if [ "$MODE" = "link" ]; then
        ln -s "$SRC" "$dest"
        echo "linked   $label  $dest -> $SRC"
      else
        mkdir -p "$dest"
        # Ship the skill only -- no VCS metadata, no editor cruft.
        cp "$SRC/SKILL.md" "$dest/SKILL.md"
        [ -d "$SRC/references" ] && cp -R "$SRC/references" "$dest/references"
        [ -f "$SRC/LICENSE" ] && cp "$SRC/LICENSE" "$dest/LICENSE"
        echo "copied   $label  $dest"
      fi
      installed=$((installed + 1))
      ;;
  esac
done

[ "$ACTION" = "list" ] && exit 0

echo
if [ "$ACTION" = "install" ] && [ "$installed" -gt 0 ]; then
  echo "Installed $SKILL_NAME ($MODE, $SCOPE scope)."
  echo "Start a fresh agent session, then ask it to \"orchestrate\" a feature."
  echo
  echo "Before your first real run, read references/git-workflow.md -- the branch,"
  echo "commit, and PR rules in this skill are opinionated and meant to be edited."
fi
[ "$skipped" -gt 0 ] && echo "($skipped target(s) skipped.)"
exit 0
