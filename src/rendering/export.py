from __future__ import annotations
from typing import Callable
import Metal

from color import Color
from ecs.entity import Entity
from ecs.system import SystemsGroup, for_each
from ecs.world import World
from recorder import FFmpegRecorder
from scenarios.types import Scenario

from .state import RenderingState


def create(
    texture: Metal.MTLTexture,
    device: Metal.MTLDeivce,
    recorder: FFmpegRecorder,
    create_pool: Callable,
    *,
    width: int,
    height: int,
    background_color: Color,
):
    recorder.start()

    bytes_per_pixel = 4
    bytes_per_row = width * bytes_per_pixel

    def create_buffer():
        buffer_size = bytes_per_row * height

        return device.newBufferWithLength_options_(
            buffer_size, Metal.MTLResourceStorageModeShared
        )

    rent_buffer, release_buffer = create_pool(create_buffer)

    @for_each
    def set_descriptor(_: World, __: Entity, state: RenderingState):
        descriptor = Metal.MTLRenderPassDescriptor.alloc().init()
        color_attachment = descriptor.colorAttachments().objectAtIndexedSubscript_(0)
        color_attachment.setTexture_(texture)
        color_attachment.setLoadAction_(Metal.MTLLoadActionClear)
        color_attachment.setStoreAction_(Metal.MTLStoreActionStore)
        color_attachment.setClearColor_(
            Metal.MTLClearColorMake(
                background_color.r,
                background_color.g,
                background_color.b,
                background_color.a,
            )
        )

        state.descriptor = descriptor

    @for_each
    def clean_buffer(_: World, __: Entity, state: RenderingState):
        buffer = rent_buffer()

        blit = state.buffer.blitCommandEncoder()
        blit.copyFromTexture_sourceSlice_sourceLevel_sourceOrigin_sourceSize_toBuffer_destinationOffset_destinationBytesPerRow_destinationBytesPerImage_(
            texture,
            0,
            0,
            Metal.MTLOriginMake(0, 0, 0),
            Metal.MTLSizeMake(width, height, 1),
            buffer,
            0,
            bytes_per_row,
            bytes_per_row * height,
        )
        blit.endEncoding()

        def on_complete(_):
            try:
                contents = buffer.contents()
                buffer_total_bytes = bytes_per_row * height
                buffer_data = contents.as_buffer(buffer_total_bytes)
                recorder.write_frame(buffer_data)
            except Exception as e:
                import traceback

                print(f"[ERROR] Frame callback failed: {e}")
                traceback.print_exc()
            finally:
                release_buffer(buffer)

        state.buffer.addCompletedHandler_(on_complete)
        state.buffer.commit()
        state.buffer = None

    return Scenario(
        SystemsGroup([], [], []),
        SystemsGroup([], [], []),
        rendering=SystemsGroup([set_descriptor], [], [clean_buffer]),
    )
