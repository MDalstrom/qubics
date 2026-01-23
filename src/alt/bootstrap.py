def get_config():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--api')
    return parser.parse_args()

def get_run(config = get_config()):
    if config.api == 'metal':
        from src.alt.metal_deps import run
        return run
    raise 
    
def get_tick():
    import src.alt.soft_body as scene
    return scene
