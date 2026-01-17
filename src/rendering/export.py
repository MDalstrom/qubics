from __future__ import annotations
from typing import Callable
import ctypes
import threading
import Metal

from ecs.entity import Entity
from ecs.system import SystemsGroup, for_each
from ecs.world import World
from recorder import FFmpegRecorder
from scenarios.types import Scenario

from .factory import RenderingState

def create(
    texture: Metal.MTLTexture,
    device: Metal.MTLDeivce,
    recorder: FFmpegRecorder,
    create_pool: Callable,
    *,
    width: int, height: int,
):
    recorder.start()

    bytes_per_pixel = 4
    bytes_per_row = ((width * bytes_per_pixel + 255) & ~255)
    
    def create_buffer():
        buffer_size = bytes_per_row * height

        return device.newBufferWithLength_options_(
            buffer_size,
            Metal.MTLResourceStorageModeShared
        )
    rent_buffer, release_buffer = create_pool(create_buffer)

    @for_each
    def set_descriptor(_: World, __: Entity, state: RenderingState):
        descriptor = Metal.MTLRenderPassDescriptor.alloc().init()
        color_attachment = descriptor.colorAttachments().objectAtIndexedSubscript_(0)
        color_attachment.setTexture_(texture)
        color_attachment.setLoadAction_(Metal.MTLLoadActionClear)
        color_attachment.setStoreAction_(Metal.MTLStoreActionStore)
        color_attachment.setClearColor_(Metal.MTLClearColorMake(0.1, 0.1, 0.15, 1.0))
        
        state.descriptor = descriptor

    @for_each
    def clean_buffer(_: World, __: Entity, state: RenderingState):
        buffer = rent_buffer()

        blit = state.buffer.blitCommandEncoder()
        blit.copyFromTexture_sourceSlice_sourceLevel_sourceOrigin_sourceSize_toBuffer_destinationOffset_destinationBytesPerRow_destinationBytesPerImage_(
            texture,
            0, 0,
            Metal.MTLOriginMake(0, 0, 0),
            Metal.MTLSizeMake(width, height, 1),
            buffer,
            0,
            bytes_per_row,
            bytes_per_row * height
        )
        blit.endEncoding()
        
        def on_complete(_):
            contents = buffer.contents()
            buffer_total_bytes = bytes_per_row * height
            buffer_data = contents.as_buffer(buffer_total_bytes)
            
            if bytes_per_row != width * 4:
                rows = []
                for y in range(height):
                    row_start = y * bytes_per_row
                    row_end = row_start + (width * 4)
                    rows.append(buffer_data[row_start:row_end])
                data = b''.join(rows)
            else:
                data = buffer_data
            
            recorder.write_frame(data)
            release_buffer(buffer)

        state.buffer.addCompletedHandler_(on_complete)
        state.buffer.commit()
        state.buffer = None

    return Scenario(
        SystemsGroup([], [], []),
        SystemsGroup([], [], []),
        rendering=SystemsGroup([set_descriptor], [], [clean_buffer]),
    )
