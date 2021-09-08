import argparse

import timefliptt
from timefliptt.time_tracker import Settings


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=timefliptt.__doc__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + timefliptt.__version__)

    parser.add_argument('-i', '--settings', help='Settings', default='settings.yml')

    return parser


def main():
    args = get_arguments_parser().parse_args()

    settings = Settings()
    with open(args.settings) as f:
        settings.from_file(f)


if __name__ == '__main__':
    main()
