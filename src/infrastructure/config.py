_config = {
    "width": 384,
    "height": 768,
    "bg_color": (255, 255, 255),
    "fps": 60,
    "duration": 10,
    "sim_dt": 1.0 / 120.0,
    "scenario": "scenario1",
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
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("-d", "--duration", type=int)
    parser.add_argument("-w", "--width", type=int)
    parser.add_argument("-h", "--height", type=int)
    parser.add_argument("--fps", type=int)
    parsed_config = vars(parser.parse_args())

    merged = merge(_config, parsed_config)

    return merged
