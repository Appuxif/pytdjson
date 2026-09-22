"""Command line entry points for local MCP setup and serving."""
import argparse
import sys
from typing import Optional

from telegram.mcp.auth import login_interactively
from telegram.mcp.config import ConfigurationError, load_settings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='pytdjson-mcp')
    subparsers = parser.add_subparsers(dest='command', required=True)
    login = subparsers.add_parser('login')
    login.add_argument(
        '--env-file', help='Optional dotenv file containing PYTDJSON_* settings.'
    )
    serve = subparsers.add_parser('serve')
    serve.add_argument(
        '--env-file', help='Optional dotenv file containing PYTDJSON_* settings.'
    )
    serve.add_argument(
        '--transport',
        choices=('stdio', 'streamable-http'),
        default='stdio',
        help='MCP transport (default: stdio).',
    )
    serve.add_argument(
        '--host', default='127.0.0.1', help='HTTP host (default: 127.0.0.1).'
    )
    serve.add_argument(
        '--port', type=int, default=8765, help='HTTP port (default: 8765).'
    )
    serve.add_argument(
        '--path', default='/mcp', help='Streamable HTTP path (default: /mcp).'
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        settings = load_settings(args.env_file)
        if args.command == 'login':
            login_interactively(settings)
            print('Telegram authorization completed.')
            return 0
        try:
            from telegram.mcp.server import create_server
            from telegram.mcp.runtime import TelegramRuntime
        except ImportError as error:
            raise ConfigurationError(
                'MCP serving requires `pip install pytdjson[mcp]`.'
            ) from error
        if args.transport == 'streamable-http':
            endpoint = f'http://{args.host}:{args.port}{args.path}'
            print(
                f'pytdjson-mcp: starting Streamable HTTP server at {endpoint}...',
                file=sys.stderr,
                flush=True,
            )
            ready_message = f'pytdjson-mcp: ready at {endpoint}.'
        else:
            print(
                'pytdjson-mcp: starting Telegram client...',
                file=sys.stderr,
                flush=True,
            )
            ready_message = 'pytdjson-mcp: ready; waiting for MCP requests.'
        runtime = TelegramRuntime(
            settings,
            on_ready=lambda: print(
                ready_message,
                file=sys.stderr,
                flush=True,
            ),
        )
        server = create_server(settings, runtime)
        if args.transport == 'streamable-http':
            server.run(
                transport='streamable-http',
                host=args.host,
                port=args.port,
                streamable_http_path=args.path,
            )
        else:
            server.run(transport='stdio')
        return 0
    except KeyboardInterrupt:
        return 0
    except (ConfigurationError, RuntimeError) as error:
        print(f'pytdjson-mcp: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
