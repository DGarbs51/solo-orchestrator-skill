#!/usr/bin/env python3
"""Install the explicit Solo command and hide automatic skill invocation in OpenCode v1."""
import argparse
import json
import os
import tempfile
from pathlib import Path
import sys

NAME = 'solo-orchestrator'


def write_json(path, value):
    """Replace one file atomically, retaining existing permissions."""
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        if path.exists():
            os.fchmod(fd, path.stat().st_mode & 0o777)
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config-dir', type=Path, required=True)
    parser.add_argument('--skill-dir', type=Path, required=True)
    parser.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()
    path = args.config_dir / 'opencode.json'
    state = args.config_dir / '.solo-orchestrator-install.json'
    if (args.config_dir / 'opencode.jsonc').exists():
        raise ValueError('opencode.jsonc exists; merge the explicit-only configuration manually (see README)')
    config = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError('OpenCode configuration must be an object')
    original = json.loads(state.read_text()) if state.exists() else None
    if args.uninstall:
        if original is None:
            print('OpenCode: no owned configuration to remove')
            return
        # Restore only our exact unchanged entries; retain later user edits.
        for group, values in original['entries'].items():
            container = config
            parts = group.split('.')
            for part in parts:
                container = container.get(part, {}) if isinstance(container, dict) else {}
            if isinstance(container, dict) and container.get(NAME) == values['installed']:
                if values['existed']:
                    container[NAME] = values['previous']
                else:
                    container.pop(NAME, None)
        write_json(path, config)
        state.unlink()
        print('OpenCode: removed owned command and skill permission')
        return
    permission = config.setdefault('permission', {})
    if not isinstance(permission, dict):
        raise ValueError('scalar permission configuration requires a manual merge (see README)')
    skills = permission.setdefault('skill', {})
    commands = config.setdefault('command', {})
    if not isinstance(skills, dict) or not isinstance(commands, dict):
        raise ValueError('scalar skill/command configuration requires a manual merge (see README)')
    command = {'description': 'Explicitly run Solo orchestration', 'template':
        'The user explicitly invoked the solo-orchestrator skill. Read and follow '
        + str(args.skill_dir.absolute() / 'SKILL.md')
        + '. Resolve its references and scripts relative to that skill directory.\nRequest: $ARGUMENTS'}
    entries = {'permission.skill': (skills, 'deny'), 'command': (commands, command)}
    if original is None:
        # Do not replace a pre-existing custom command.
        if NAME in commands and commands[NAME] != command:
            raise ValueError('a custom /solo-orchestrator command already exists; refusing to replace it')
        original = {'entries': {group: {'existed': NAME in container,
                    'previous': container.get(NAME), 'installed': value}
                    for group, (container, value) in entries.items()}}
    else:
        for group, (container, value) in entries.items():
            saved = original['entries'][group]
            pending = (NAME in container) == saved['existed'] and container.get(NAME) == saved['previous']
            if container.get(NAME) != saved['installed'] and not pending:
                raise ValueError('owned OpenCode settings were modified; reconcile them manually')
            original['entries'][group]['installed'] = value
    for container, value in entries.values():
        container[NAME] = value
    args.config_dir.mkdir(parents=True, exist_ok=True)
    # State is saved first so an interrupted initial install retains prior values.
    write_json(state, original)
    write_json(path, config)
    print('OpenCode: explicit /solo-orchestrator command configured')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'OpenCode setup: {exc}', file=sys.stderr)
        sys.exit(1)
