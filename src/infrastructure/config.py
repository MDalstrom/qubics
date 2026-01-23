from color import Color


_config = {
    "bg_color": (255, 255, 255),
    "fps": 60,
    "timedelta": 1.0 / 60.0,
    "timescale": 1,
    "scenario": "scenario1",
    "virtual_width": 2700,
    "virtual_height": 4800,
    "debug": False,
    "background-color": Color(0, 0, 0, 1),
}


def get_config():
    def merge(base: dict, override: dict, path=[]):
        for key in override:
            if key in base:
                if isinstance(base[key], dict) and isinstance(override[key], dict):
                    merge(base[key], override[key], path + [str(key)])
                elif override[key] is not None:
                    base[key] = override[key]
            else:
                base[key] = override[key]
        return base

    import argparse

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-o", "--output", type=str, nargs='?')
    parser.add_argument("-d", "--duration", type=int)
    parser.add_argument("-w", "--width", type=int)
    parser.add_argument("-h", "--height", type=int)
    parser.add_argument("--debug")
    parser.add_argument("--watch")
    parser.add_argument("--fps", type=int)
    parsed_config = vars(parser.parse_args())

    merged = merge(_config, parsed_config)

    return merged
