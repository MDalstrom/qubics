from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import Cocoa
import Metal
import MetalKit
import objc
from pathlib import Path
import Foundation


frame = Cocoa.NSMakeRect(0, 0, 800, 600)
color = Metal.MTLClearColorMake(0, 0, 0, 1)


def view_delegate_fc(device, tick):
    class ViewDelegate(Cocoa.NSObject):
        def initWithDevice_tick_(self, device, tick):
            self = objc.super(ViewDelegate, self).init()
            if self is None:
                return None

            self.commandQueue = device.newCommandQueue()
            self.tick = tick

            return self

        def drawInMTKView_(self, view):
            drawable = view.currentDrawable()
            if drawable is None:
                return
            cb = self.commandQueue.commandBuffer()
            self.tick(command_buffer=cb)
            cb.presentDrawable_(drawable)
            cb.commit()

        def mtkView_drawableSizeWillChange_(self, view, size):
            pass
    return ViewDelegate.alloc().initWithDevice_tick_(device, tick)


def device_fc():
    return Metal.MTLCreateSystemDefaultDevice()


def library_fc(device):
    library_path = (
        Path(__file__).resolve().parent.parent.parent
        / "build" / "default.metallib"
    )
    url = Foundation.NSURL.fileURLWithPath_(str(library_path))
    library, error = device.newLibraryWithURL_error_(url, None)
    assert not error
    return library


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
    return window


def app_delegate_fc():
    class AppDelegate(Cocoa.NSObject):
        def applicationShouldTerminateAfterLastWindowClosed_(self, app):
            return True
    return AppDelegate.alloc().init()


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

@dataclass
class State:
    device: Metal.MTLDevice
    window: Cocoa.NSWindow
    app: Cocoa.NSApplication
    view: MetalKit.MTKView

def run(state: State, tick) -> None:
    view_delegate = view_delegate_fc(state.device, tick)
    app_delegate = app_delegate_fc()

    state.app.setDelegate_(app_delegate)
    state.view.setDelegate_(view_delegate)
    state.view.setPaused_(False)
    state.view.setEnableSetNeedsDisplay_(False)
    state.window.setContentView_(state.view)
    state.window.center()
    state.window.makeKeyAndOrderFront_(None)

    def window_will_close(notification):
        state.app.terminate_(None)

    Cocoa.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
        None,
        objc.selector(window_will_close, signature=b"v@:@"),
        Cocoa.NSWindowWillCloseNotification,
        state.window,
    )

    return state.app.run()

