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
    view: MetalKit.MTKView | None
    resolution: tuple[int, int]
    size: tuple[int, int]
    device: object = None
    offscreen_texture: object = None


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


def create_export_system(writer, resolution: tuple[int, int], size: tuple[int, int]):
    """Create a system that renders frames offscreen and writes them to a video file."""
    device = Metal.MTLCreateSystemDefaultDevice()
    if device is None:
        raise RuntimeError("Metal is not supported on this system")
    
    # Create offscreen texture for rendering
    texture_descriptor = Metal.MTLTextureDescriptor.alloc().init()
    texture_descriptor.setTextureType_(Metal.MTLTextureType2D)
    texture_descriptor.setPixelFormat_(Metal.MTLPixelFormatBGRA8Unorm)
    texture_descriptor.setWidth_(resolution[0])
    texture_descriptor.setHeight_(resolution[1])
    texture_descriptor.setUsage_(Metal.MTLTextureUsageRenderTarget | Metal.MTLTextureUsageShaderRead)
    
    offscreen_texture = device.newTextureWithDescriptor_(texture_descriptor)
    
    viewport_entity = Entity()
    viewport_entity.add_component(MetalViewport(
        view=None,
        resolution=resolution,
        size=size,
        device=device,
        offscreen_texture=offscreen_texture
    ))
    viewport_entity.add_component(Transform(x=0, y=0))
    
    @for_each
    def export_system(_: World, __: Entity, viewport: MetalViewport):
        if viewport.view is not None:
            return
        
        # Read pixels from texture
        width = resolution[0]
        height = resolution[1]
        bytes_per_row = width * 4
        region = Metal.MTLRegionMake2D(0, 0, width, height)
        
        import array
        pixel_data = array.array('B', [0] * (bytes_per_row * height))
        
        viewport.offscreen_texture.getBytes_bytesPerRow_fromRegion_mipmapLevel_(
            pixel_data,
            bytes_per_row,
            region,
            0
        )
        
        import numpy as np
        bgra_array = np.frombuffer(pixel_data, dtype=np.uint8).reshape((height, width, 4))
        rgb_array = bgra_array[:, :, [2, 1, 0]]
        
        writer.send(rgb_array.tobytes())
    
    return export_system, viewport_entity

