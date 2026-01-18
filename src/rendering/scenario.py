from __future__ import annotations

from application.transform import Transform
from rendering.shape import draw_shape_system
from ecs.entity import Entity
from ecs.world import World
from ecs.system import for_each, SystemsGroup
from scenarios.types import Scenario

from .state import RenderingState

import Metal
import Cocoa


def create(
    device: Metal.MTLDevice, pipeline_state: Metal.MTLRenderingPipelineState,
    *,
    width: int, height: int
) -> Scenario:

    def bake(world: World):
        queue = device.newCommandQueue()

        e = Entity("RenderingState")
        e.add_component(RenderingState(device, queue, None, None, None))
        e.add_component(Transform(0, 0, scale_x=width, scale_y=height))
        world.add(e)

    def handle_events(world: World):
        app = Cocoa.NSApplication.sharedApplication()
        while True:
            event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
                Cocoa.NSEventMaskAny,
                Cocoa.NSDate.distantPast(),
                Cocoa.NSDefaultRunLoopMode,
                True,
            )
            if event is None:
                break

            if event.type() == Cocoa.NSEventTypeKeyDown:
                if event.keyCode() == 53:  # ESC key
                    raise KeyboardInterrupt

            app.sendEvent_(event)
            app.updateWindows()

    @for_each
    def set_encoder(_: World, __: Entity, state: RenderingState):
        buffer = state.queue.commandBuffer()
        encoder = buffer.renderCommandEncoderWithDescriptor_(state.descriptor)
        encoder.setRenderPipelineState_(pipeline_state)

        state.buffer = buffer
        state.encoder = encoder

    @for_each
    def clean_encoder(_: World, __: Entity, state: RenderingState):
        state.encoder.endEncoding()
        state.encoder = None

    return Scenario(
        bake=SystemsGroup([], [bake], []),
        simulation=SystemsGroup([], [], []),
        rendering=SystemsGroup([handle_events], [set_encoder, draw_shape_system], [clean_encoder]),
    )
