from __future__ import annotations
from dataclasses import dataclass
import Cocoa
import Metal
import MetalKit
import Quartz
import objc
from pathlib import Path
import Foundation
from q_engine import keys


frame = Cocoa.NSMakeRect(0, 0, 800, 800)
color = Metal.MTLClearColorMake(0, 0, 0, 1)


def mk_view_delegate(device, tick):
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


def mk_device():
    return Metal.MTLCreateSystemDefaultDevice()


def mk_library(device):
    library_path = (
        Path(__file__).resolve().parent.parent.parent / "build" / "default.metallib"
    )
    url = Foundation.NSURL.fileURLWithPath_(str(library_path))
    library, error = device.newLibraryWithURL_error_(url, None)
    assert library, error
    return library


def mk_view(device) -> MetalKit.MTKView:
    class View(MetalKit.MTKView):
        def initWithFrame_device_(self, frame, device):
            self = objc.super(View, self).initWithFrame_device_(frame, device)
            self.setupMouseTracking()
            return self

        def acceptsFirstResponder(self):
            return True

        def setupMouseTracking(self):
            options = (
                Cocoa.NSTrackingActiveInKeyWindow
                | Cocoa.NSTrackingMouseMoved
                | Cocoa.NSTrackingInVisibleRect
            )

            tracking_area = (
                Cocoa.NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                    self.bounds(), options, self, None
                )
            )
            self.addTrackingArea_(tracking_area)

        def flagsChanged_(self, event):
            keys.update_modifier_keys(event.modifierFlags())

        def mouseMoved_(self, event):
            keys.set_mouse_delta((event.deltaX(), event.deltaY()))

        def keyDown_(self, event):
            keys.update_modifier_keys(event.modifierFlags())
            keys.down(event)

        def keyUp_(self, event):
            keys.update_modifier_keys(event.modifierFlags())
            keys.up(event)
    view = View.alloc().initWithFrame_device_(frame, device)

    view.setColorPixelFormat_(Metal.MTLPixelFormatBGRA8Unorm)
    view.setClearColor_(color)
    view.setPaused_(False)
    view.setEnableSetNeedsDisplay_(False)
    view.setPreferredFramesPerSecond_(60)
    
    Cocoa.NSCursor.hide()
    Quartz.CoreGraphics.CGAssociateMouseAndMouseCursorPosition(False)

    return view


def mk_window():
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


def mk_app_delegate():
    class AppDelegate(Cocoa.NSObject):
        def applicationShouldTerminateAfterLastWindowClosed_(self, app):
            return True

        def windowDidBecomeKey_(self, notification):
            notification.object().setAcceptsMouseMovedEvents_(True)
            notification.object().setShowsToolbarButton_(False)

        def windowDidResignKey_(self, notification):
            notification.object().setAcceptsMouseMovedEvents_(False)

    return AppDelegate.alloc().init()


def mk_app():
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
    view_delegate = mk_view_delegate(state.device, tick)
    app_delegate = mk_app_delegate()

    state.app.setDelegate_(app_delegate)
    state.view.setDelegate_(view_delegate)

    state.view.setPaused_(False)
    state.view.setEnableSetNeedsDisplay_(False)
    state.window.setContentView_(state.view)
    state.window.center()
    state.window.makeKeyAndOrderFront_(None)

    notification_center = Cocoa.NSNotificationCenter.defaultCenter()

    def window_will_close(notification):
        state.app.terminate_(None)

    notification_center.addObserver_selector_name_object_(
        None,
        objc.selector(window_will_close, signature=b"v@:@"),
        Cocoa.NSWindowWillCloseNotification,
        state.window,
    )

    return state.app.run()
