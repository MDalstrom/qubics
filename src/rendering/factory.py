from __future__ import annotations
from pathlib import Path
from typing import Callable

import Cocoa
import Metal
import MetalKit
import Foundation
from PyObjCTools.AppHelper import objc


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

def create_view(
    device: Metal.MTLDevice,
    loop: Callable[[float], float],
    rect: tuple,
    background_color: tuple,
):
    class ViewDelegate(Cocoa.NSObject):
        def init(self):
            self = objc.super(ViewDelegate, self).init()
            self.acc = 0.0
            return self
        def mtkView_drawableSizeWillChange_(self, view, size):
            pass
        def drawInMTKView_(self, view):
            self.acc = loop(self.acc)

    rect_obj = Cocoa.NSMakeRect(*rect)
    color_obj = Metal.MTLClearColorMake(*background_color)
    
    app = Cocoa.NSApplication.sharedApplication()
    app.setActivationPolicy_(Cocoa.NSApplicationActivationPolicyRegular)

    window = Cocoa.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect_obj,
        Cocoa.NSWindowStyleMaskTitled | Cocoa.NSWindowStyleMaskClosable | Cocoa.NSWindowStyleMaskResizable,
        Cocoa.NSBackingStoreBuffered,
        False,
    )
    window.setTitle_("Metal Viewport")
    window.center()
    
    view = MetalKit.MTKView.alloc().initWithFrame_device_(rect_obj, device)
    view.setClearColor_(color_obj)
    view_delegate = ViewDelegate.alloc().init()
    view.setDelegate_(view_delegate)
    global _py_delegate
    _py_delegate = view_delegate

    window.setContentView_(view)
    window.makeKeyAndOrderFront_(None)
    app.activateIgnoringOtherApps_(True)

    return view


def create_texture(device: Metal.MTLDevice, *, width: int, height: int):
    descriptor = Metal.MTLTextureDescriptor.alloc().init()
    descriptor.setTextureType_(Metal.MTLTextureType2D)
    descriptor.setPixelFormat_(Metal.MTLPixelFormatBGRA8Unorm)
    descriptor.setWidth_(width)
    descriptor.setHeight_(height)
    descriptor.setUsage_(
        Metal.MTLTextureUsageRenderTarget | Metal.MTLTextureUsageShaderRead
    )
    texture = device.newTextureWithDescriptor_(descriptor)
    return texture


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


