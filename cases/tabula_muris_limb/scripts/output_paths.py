"""Keep new runs, state pointers and collected outputs away from frozen results."""
from pathlib import Path


def output_root(parser, base):
    parser.add_argument('--output-root', type=Path, default=base / 'runs',
                        help='New run/state/deliverable root (default: case/runs).')


def prepare_root(path):
    root = path.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root
