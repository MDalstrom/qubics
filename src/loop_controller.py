"""
Single loop controller responsible for:
- Time accumulation
- Fixed simulation stepping
- Calling renderers with interpolation alpha
"""
from clock import Clock
from simulation import SimulationState, UpdateFn
from renderer import BackendRenderer, create_renderer


def run_game_loop(
    state: SimulationState,
    update: UpdateFn,
    backend: BackendRenderer,
    render_fns: list,
    clock: Clock,
    sim_dt: float,
    max_frame_time: float = 0.25
) -> None:
    """
    Main game loop with fixed timestep simulation and interpolated rendering.
    
    Args:
        state: Simulation state (current + previous)
        update: Simulation update function
        backend: Rendering backend (pygame window or video)
        render_fns: List of render functions
        clock: Time function (real-time or deterministic)
        sim_dt: Fixed simulation timestep
        max_frame_time: Max frame time to prevent spiral of death
    """
    render = create_renderer(state.world, render_fns)
    
    current_time = clock()
    accumulator = 0.0
    
    while not backend.should_quit():
        # Calculate frame time
        new_time = clock()
        frame_time = new_time - current_time
        if frame_time > max_frame_time:
            frame_time = max_frame_time
        current_time = new_time
        accumulator += frame_time
        
        # Fixed timestep simulation updates
        while accumulator >= sim_dt:
            state.save_previous()
            update(sim_dt)
            accumulator -= sim_dt
        
        # Calculate interpolation alpha
        alpha = accumulator / sim_dt
        
        # Render with interpolation
        backend.begin_frame()
        from domain import RenderContext
        surface = backend.get_surface()
        context = RenderContext(surface, alpha)
        render(context)
        backend.end_frame()


def run_fixed_frames(
    state: SimulationState,
    update: UpdateFn,
    backend: BackendRenderer,
    render_fns: list,
    sim_dt: float,
    frame_dt: float,
    total_frames: int
) -> None:
    """
    Run fixed number of frames deterministically (for video export).
    
    Args:
        state: Simulation state
        update: Simulation update function
        backend: Rendering backend
        render_fns: List of render functions
        sim_dt: Fixed simulation timestep
        frame_dt: Frame duration (1/fps)
        total_frames: Total frames to render
    """
    render = create_renderer(state.world, render_fns)
    accumulator = 0.0
    
    for frame_num in range(total_frames):
        # Add fixed time increment
        accumulator += frame_dt
        
        # Fixed timestep simulation updates
        while accumulator >= sim_dt:
            state.save_previous()
            update(sim_dt)
            accumulator -= sim_dt
        
        # Calculate interpolation alpha
        alpha = accumulator / sim_dt
        
        # Render with interpolation
        backend.begin_frame()
        from domain import RenderContext
        surface = backend.get_surface()
        context = RenderContext(surface, alpha)
        render(context)
        backend.end_frame()
        
        if hasattr(backend, 'report_progress'):
            backend.report_progress(frame_num, total_frames)
