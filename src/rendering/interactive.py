from __future__ import annotations
import Cocoa
import Metal
import MetalKit

from ecs.entity import Entity
from ecs.system import SystemsGroup, for_each
from ecs.world import World
from scenarios.types import Scenario

from .factory import RenderingState


def create_view(
    device: Metal.MTLDevice,
    delegate: MetalKit.MTKViewDelegate,
    *,
    rect: Cocoa.NSMakeRect,
    background_color: Metal.MTLClearColorMake,
):
    app = Cocoa.NSApplication.sharedApplication()
    app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyRegular)

    window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect,
        Cocoa.NSWindowStyleMaskTitled | Cocoa.NSClosableWindowMask,
        Cocoa.NSBackingStoreBuffered,
        False,
    )
    window.setTitle_("Metal Viewport")
    window.center()

    view = MetalKit.MTKView.alloc().initWithFrame_device_(rect, device)
    view.setClearColor_(background_color)
    view.setDelegate_(delegate)

    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)
    app.activateIgnoringOtherApps_(True)

    return view


def create(view: MetalKit.MTKView):
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
        rendering=SystemsGroup([set_descriptor], [], [clean_buffer]),
    )
