"""Generate or install a project-local MCP connection without credentials."""
import json
import os
import sys
from pathlib import Path


def configuration():
    root = str(Path(__file__).resolve().parent.parent)
    code = f"import sys; sys.path.insert(0, {root!r}); from agentgrinder.mcp_server import main; main()"
    return {'command': sys.executable, 'args': ['-c', code]}


def add_parser(sub):
    p = sub.add_parser('connect', help='connect a project to Grinder through MCP')
    p.add_argument('client', choices=['cursor', 'claude'])
    p.add_argument('--project', default='.', help='project folder')
    p.add_argument('--install', action='store_true', help='merge the connection into the project config')


def run_cli(args):
    config = configuration()
    if not args.install:
        print(json.dumps({'mcpServers': {'agentgrinder': config}}, indent=2))
        return 0
    project = Path(args.project).expanduser().resolve()
    target = project / ('.cursor/mcp.json' if args.client == 'cursor' else '.mcp.json')
    try:
        original = target.read_text() if target.exists() else None
        existing = json.loads(original) if original is not None else {}
        if not isinstance(existing, dict) or not isinstance(existing.get('mcpServers', {}), dict):
            raise ValueError('MCP config must contain an object of servers')
        servers = existing.setdefault('mcpServers', {})
        if 'agentgrinder' in servers and servers['agentgrinder'] != config:
            raise ValueError('An Agent Grinder connection already exists. Review it before replacing it.')
        servers['agentgrinder'] = config
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.grinder-tmp')
        # Exclusive create avoids overwriting a concurrent edit or an unrelated temp file.
        with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as stream:
            stream.write(json.dumps(existing, indent=2) + '\n')
        if (target.read_text() if target.exists() else None) != original:
            temporary.unlink()
            raise ValueError('The MCP config changed during setup. Retry after the other edit finishes.')
        temporary.replace(target)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f'Connected in {target}. Reload the client and ask it to preview your latest run. No credential was added.')
    return 0
