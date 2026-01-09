"""
Abstract renderer interface and implementations.
Renderers receive world state and alpha for interpolation.
Renderers never mutate simulation state.
"""
from typing import Protocol
from domain import World, RenderContext, Entity


class RenderFn(Protocol):
    """Renders entity with interpolation alpha."""
    def __call__(self, context: RenderContext, entity: Entity) -> None:
        ...


class BackendRenderer(Protocol):
    """Backend-specific rendering interface."""
    def begin_frame(self) -> None:
        ...
    
    def render(self, world: World, alpha: float, render_fns: list[RenderFn]) -> None:
        ...
    
    def end_frame(self) -> None:
        ...
    
    def should_quit(self) -> bool:
        ...


def create_renderer(world: World, render_fns: list[RenderFn]):
    """Create rendering function that uses render_fns."""
    
    def render(context: RenderContext) -> None:
        from components import Destroyed
        for renderer_fn in render_fns:
            for entity in world:
                if entity.get_component(Destroyed):
                    continue
                renderer_fn(context, entity)
    
    return render
