from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from pathlib import Path

import Cocoa
import Metal
import Foundation
import objc

from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each, SystemsGroup
from ecs.world import World
from scenarios.types import Scenario


def create_delegate():
    class Delegate(Cocoa.NSObject):
        def init(self):
            self = objc.super(Delegate, self).init()
            if self is None:
                return None
            return self

        def mtkView_drawableSizeWillChange_(self, view, size):
            pass

        def drawInMTKView_(self, view):
            drawable = view.currentDrawable()
            if drawable is None:
                return

            descriptor = view.currentRenderPassDescriptor()
            if descriptor is None:
                return

            command_queue = view.device().newCommandQueue()
            command_buffer = command_queue.commandBuffer()
            encoder = command_buffer.renderCommandEncoderWithDescriptor_(descriptor)
            encoder.endEncoding()
            command_buffer.presentDrawable_(drawable)
            command_buffer.commit()

    return Delegate()


def create_device():
    device = Metal.MTLCreateSystemDefaultDevice()
    return device


def create_library(device: Metal.MTLDevice):
    library_path = Path(__file__).resolve().parent.parent.parent
    library_path = library_path / "build" / "default.metallib"
    url = Foundation.NSURL.fileURLWithPath_(str(library_path))
    library, error = device.newLibraryWithURL_error_(url, None)
    assert not error
    return library


def create_pipeline(
    library: Metal.MTLLibrary,
    device: Metal.MTLDevice,
    *,
    vertex_fn_name: str,
    fragment_fn_name: str,
):
    descriptor = Metal.MTLRenderPipelineDescriptor.alloc().init()

    vertex_fn = library.newFunctionWithName_(vertex_fn_name)
    fragment_fn = library.newFunctionWithName_(fragment_fn_name)

    descriptor.setVertexFunction_(vertex_fn)
    descriptor.setFragmentFunction_(fragment_fn)

    color_attachment = descriptor.colorAttachments().objectAtIndexedSubscript_(0)
    color_attachment.setPixelFormat_(Metal.MTLPixelFormatBGRA8Unorm)
    color_attachment.setBlendingEnabled_(True)
    color_attachment.setRgbBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setAlphaBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setSourceRGBBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setSourceAlphaBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setDestinationRGBBlendFactor_(
        Metal.MTLBlendFactorOneMinusSourceAlpha
    )
    color_attachment.setDestinationAlphaBlendFactor_(
        Metal.MTLBlendFactorOneMinusSourceAlpha
    )

    state, error = device.newRenderPipelineStateWithDescriptor_error_(descriptor, None)
    assert not error
    return state


@dataclass
class RenderingState:
    device: Metal.MTLDevice
    queue: Metal.MTLCommandQueue
    buffer: Metal.MTLCommandBuffer
    encoder: Metal.MTLRenderCommandEncoder
    descriptor: Any


def create(
    device: Metal.MTLDevice, pipeline_state: Metal.MTLRenderingPipelineState
) -> Scenario:

    def bake(world: World):
        queue = device.newCommandQueue()

        e = Entity("RenderingState")
        e.add_component(RenderingState(device, queue, None, None, None))
        e.add_component(Transform(0, 0, scale_x=900, scale_y=1600))
        world.add(e)

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
        rendering=SystemsGroup([], [set_encoder], [clean_encoder]),
    )
