from dataclasses import dataclass
import Metal
import MetalKit
import Cocoa
import objc
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@dataclass
class MetalViewport:
    view: MetalKit.MTKView
    resolution: tuple[int, int]
    size: tuple[int, int]  # Virtual size for rendering


class MetalViewDelegate(Cocoa.NSObject):
    def init(self):
        self = objc.super(MetalViewDelegate, self).init()
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


def handle_events(world: World):
    app = Cocoa.NSApplication.sharedApplication()
    while True:
        event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
            Cocoa.NSEventMaskAny,
            Cocoa.NSDate.distantPast(),
            Cocoa.NSDefaultRunLoopMode,
            True
        )
        if event is None:
            break
        
        if event.type() == Cocoa.NSEventTypeKeyDown:
            if event.keyCode() == 53:  # ESC key
                raise KeyboardInterrupt
        
        app.sendEvent_(event)
        app.updateWindows()


def create_interactive_system(resolution: tuple[int, int], size: tuple[int, int]):
    device = Metal.MTLCreateSystemDefaultDevice()
    if device is None:
        raise RuntimeError("Metal is not supported on this system")
    
    app = Cocoa.NSApplication.sharedApplication()
    app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyRegular)
    
    window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        Cocoa.NSMakeRect(0, 0, resolution[0], resolution[1]),
        Cocoa.NSWindowStyleMaskTitled | Cocoa.NSClosableWindowMask,
        Cocoa.NSBackingStoreBuffered,
        False
    )
    window.setTitle_("Metal Viewport")
    window.center()
    
    metal_view = MetalKit.MTKView.alloc().initWithFrame_device_(
        Cocoa.NSMakeRect(0, 0, resolution[0], resolution[1]),
        device
    )
    metal_view.setClearColor_(Metal.MTLClearColorMake(0.1, 0.1, 0.15, 1.0))  # Dark blue-gray background
    
    delegate = MetalViewDelegate.alloc().init()
    metal_view.setDelegate_(delegate)
    
    window.setContentView_(metal_view)
    window.makeKeyAndOrderFront_(None)
    app.activateIgnoringOtherApps_(True)
    
    viewport_entity = Entity()
    viewport_entity.add_component(MetalViewport(view=metal_view, resolution=resolution, size=size))
    viewport_entity.add_component(Transform(x=0, y=0))
    
    @for_each
    def interactive_system(_: World, __: Entity, viewport: MetalViewport):
        viewport.view.draw()
    
    return interactive_system, viewport_entity


def create_export_system(writer, resolution: tuple[int, int]):
    @for_each
    def export_system(_: World, __: Entity, viewport: MetalViewport, transform: Transform):
        pass
    return export_system

