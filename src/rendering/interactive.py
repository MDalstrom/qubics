from __future__ import annotations
import MetalKit

from ecs.entity import Entity
from ecs.system import SystemsGroup, for_each
from ecs.world import World
from scenarios.types import Scenario
from application.transform import Transform

from .state import RenderingState


def create(view: MetalKit.MTKView):

    @for_each
    def fit_aspect(_: World, __: Entity, state: RenderingState, transform: Transform):
        x, y = view.drawableSize()
        transform.set_world_scale(x, y)

    @for_each
    def set_descriptor(_: World, __: Entity, state: RenderingState):
        state.descriptor = view.currentRenderPassDescriptor()

    @for_each
    def clean_buffer(_: World, __: Entity, state: RenderingState):
        state.buffer.presentDrawable_(view.currentDrawable())
        state.buffer.commit()
        state.buffer = None

    return Scenario(
        SystemsGroup([], [], []),
        SystemsGroup([], [], []),
        rendering=SystemsGroup([set_descriptor, fit_aspect], [], [clean_buffer]),
    )
