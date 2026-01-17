from __future__ import annotations
from typing import Callable
import Metal

from color import Color
from ecs.entity import Entity
from ecs.system import SystemsGroup, for_each
from ecs.world import World
from recorder import FFmpegRecorder
from scenarios.types import Scenario

from .factory import RenderingState

def create_texture(device: Metal.MTLDevice, *, width: int, height: int):
    descriptor = Metal.MTLTextureDescriptor.alloc().init()
    descriptor.setTextureType_(Metal.MTLTextureType2D)
    descriptor.setPixelFormat_(Metal.MTLPixelFormatBGRA8Unorm)
    descriptor.setWidth_(width)
    descriptor.setHeight_(height)
    descriptor.setUsage_(Metal.MTLTextureUsageRenderTarget | Metal.MTLTextureUsageShaderRead)
    texture = device.newTextureWithDescriptor_(descriptor)
    return texture

def create(
    texture: Metal.MTLTexture,
    device: Metal.MTLDeivce,
    recorder: FFmpegRecorder,
    create_pool: Callable,
    *,
    width: int, height: int,
    background_color: Color
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
        color_attachment.setClearColor_(Metal.MTLClearColorMake(background_color.r, background_color.g, background_color.b, background_color.a))
        
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
            try:
                contents = buffer.contents()
                buffer_total_bytes = bytes_per_row * height
                buffer_data = contents.as_buffer(buffer_total_bytes)
                
                # Debug: check actual buffer size
                actual_size = len(buffer_data)
                if actual_size != buffer_total_bytes:
                    print(f"[ERROR] Buffer size mismatch! Expected {buffer_total_bytes}, got {actual_size}")
                
                if bytes_per_row != width * 4:
                    rows = []
                    for y in range(height):
                        row_start = y * bytes_per_row
                        row_end = row_start + (width * 4)
                        if row_end > actual_size:
                            print(f"[ERROR] Row {y} out of bounds: {row_end} > {actual_size}")
                            break
                        rows.append(buffer_data[row_start:row_end])
                    data = b''.join(rows)
                else:
                    data = buffer_data
                
                expected_frame_size = width * height * 4
                if len(data) != expected_frame_size:
                    print(f"[ERROR] Frame size wrong! Expected {expected_frame_size}, got {len(data)}")
                
                if not recorder.write_frame(data):
                    print(f"[ERROR] Failed to write frame, FFmpeg may have exited")
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
