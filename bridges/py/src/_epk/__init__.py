import argparse


def main():
    parser = argparse.ArgumentParser(prog="qubics")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen = subparsers.add_parser("generate", help="generate C stubs")
    gen.add_argument("pyproject", nargs="?", default=".", type=str)
    gen.add_argument("destination", nargs="?", default=None, type=str)

    pub = subparsers.add_parser("publish", help="publish to epk registry")
    pub.add_argument("pyproject", nargs="?", default=".", type=str)

    args = parser.parse_args()
    
    if args.command == "generate":
        from _epk.generate import generate
        generate(args.pyproject, args.destination or args.pyproject)
    elif args.command == "publish":
        from _epk.publish import publish
        publish(args.pyproject)
