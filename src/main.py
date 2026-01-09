"""
Main entry point - declares universal game loop.
All dependencies injected from dependencies.py
"""
import pygame
from infrastructure.dependencies import (
    get_simulation_state,
    get_update_fn,
    get_render_fns,
    get_backend,
    get_clock,
    get_loop_params,
    get_config
)

pygame.init()

# Get all dependencies
config = get_config()
state = get_simulation_state()
update = get_update_fn()
render_fns = get_render_fns()
backend = get_backend()
loop_params = get_loop_params()

# Run universal game loop
try:
    loop_params['loop'](
        state=state,
        update=update,
        backend=backend,
        render_fns=render_fns,
        sim_dt=config['sim_dt'],
        **loop_params['extra']
    )
finally:
    backend.cleanup()

