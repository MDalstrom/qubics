from __future__ import annotations
import Cocoa
import Metal
import MetalKit
import objc
from pathlib import Path
import Foundation
from src.alt.ecs import RenderingContext


frame = Cocoa.NSMakeRect(0, 0, 800, 600)
color = Metal.MTLClearColorMake(0, 0, 0, 1)


class ViewDelegate(Cocoa.NSObject):
    def initWithDevice_pipeline_tick_(self, device, pipeline, tick):
        self = objc.super(ViewDelegate, self).init()
        if self is None:
            return None

        self.device = device
        self.pipeline = pipeline
        self.tick = tick
        self.commandQueue = device.newCommandQueue()

        return self

    def drawInMTKView_(self, view):
        drawable = view.currentDrawable()
        if drawable is None:
            return

        rpd = view.currentRenderPassDescriptor()
        cb = self.commandQueue.commandBuffer()

        encoder = cb.renderCommandEncoderWithDescriptor_(rpd)
        encoder.setRenderPipelineState_(self.pipeline)
        viewport = Metal.MTLViewport()
        viewport.originX = 0
        viewport.originY = 0
        viewport.width = view.drawableSize().width
        viewport.height = view.drawableSize().height
        viewport.znear = -1.0
        viewport.zfar = 1.0
        encoder.setViewport_(viewport)
        context = RenderingContext(device=self.device, encoder=encoder, buffer=cb)
        context.viewport_width = view.drawableSize().width
        context.viewport_height = view.drawableSize().height
        self.tick(context)
        encoder.endEncoding()

        cb.presentDrawable_(drawable)
        cb.commit()

    def mtkView_drawableSizeWillChange_(self, view, size):
        pass


def device_fc():
    return Metal.MTLCreateSystemDefaultDevice()


def library_fc(device):
    library_path = Path(__file__).resolve().parent.parent.parent
    library_path = library_path / "build" / "default.metallib"
    url = Foundation.NSURL.fileURLWithPath_(str(library_path))
    library, error = device.newLibraryWithURL_error_(url, None)
    assert not error
    return library


def pipeline_fc(
    library: Metal.MTLLibrary,
    device: Metal.MTLDevice,
):
    descriptor = Metal.MTLRenderPipelineDescriptor.alloc().init()

    vertex_fn = library.newFunctionWithName_("vertex_main")
    fragment_fn = library.newFunctionWithName_("fragment_main")

    descriptor.setVertexFunction_(vertex_fn)
    descriptor.setFragmentFunction_(fragment_fn)

    # Set up vertex descriptor for 3D position
    vertex_descriptor = Metal.MTLVertexDescriptor.alloc().init()
    vertex_descriptor.attributes().objectAtIndexedSubscript_(0).setFormat_(Metal.MTLVertexFormatFloat3)
    vertex_descriptor.attributes().objectAtIndexedSubscript_(0).setOffset_(0)
    vertex_descriptor.attributes().objectAtIndexedSubscript_(0).setBufferIndex_(0)
    vertex_descriptor.layouts().objectAtIndexedSubscript_(0).setStride_(12)
    descriptor.setVertexDescriptor_(vertex_descriptor)

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


def view_fc(device):
    view = MetalKit.MTKView.alloc().initWithFrame_device_(frame, device)

    view.setColorPixelFormat_(Metal.MTLPixelFormatBGRA8Unorm)
    view.setClearColor_(color)
    view.setPaused_(False)
    view.setEnableSetNeedsDisplay_(False)
    view.setPreferredFramesPerSecond_(60)

    return view


def window_fc():
    window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        frame,
        Cocoa.NSWindowStyleMaskTitled
        | Cocoa.NSWindowStyleMaskClosable
        | Cocoa.NSWindowStyleMaskResizable
        | Cocoa.NSWindowStyleMaskMiniaturizable,
        Cocoa.NSBackingStoreBuffered,
        False,
    )
    window.makeKeyAndOrderFront_(None)
    return window


class AppDelegate(Cocoa.NSObject):
    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        return True


def app_fc():
    app = Cocoa.NSApplication.sharedApplication()
    app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyRegular)
    app.activateIgnoringOtherApps_(True)

    menubar = Cocoa.NSMenu.alloc().init()
    app_menu = Cocoa.NSMenu.alloc().init()
    quit_item = Cocoa.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Quit", "terminate:", "q"
    )
    app_menu.addItem_(quit_item)

    app_menu_item = Cocoa.NSMenuItem.alloc().init()
    menubar.addItem_(app_menu_item)
    app.setMainMenu_(menubar)
    app_menu_item.setSubmenu_(app_menu)

    return app


def run(tick):
    device = device_fc()
    view = view_fc(device)
    library = library_fc(device)
    pipeline = pipeline_fc(library, device)
    view_delegate = ViewDelegate.alloc().initWithDevice_pipeline_tick_(
        device, pipeline, tick
    )
    app_delegate = AppDelegate.alloc().init()
    app = app_fc()
    window = window_fc()

    app.setDelegate_(app_delegate)
    view.setDelegate_(view_delegate)
    view.setPaused_(False)
    view.setEnableSetNeedsDisplay_(False)
    window.setContentView_(view)
    window.center()

    def window_will_close(notification):
        app.terminate_(None)

    Cocoa.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
        None,
        objc.selector(window_will_close, signature=b"v@:@"),
        Cocoa.NSWindowWillCloseNotification,
        window,
    )

    app.run()
    return view, view_delegate, app, window
