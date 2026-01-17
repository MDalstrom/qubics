import Cocoa
from ecs.world import World


def handle_events(world: World):
    app = Cocoa.NSApplication.sharedApplication()
    while True:
        event = app.nextEventMatchingMask_untilDate_inMode_dequeue_(
            Cocoa.NSEventMaskAny,
            Cocoa.NSDate.distantPast(),
            Cocoa.NSDefaultRunLoopMode,
            True,
        )
        if event is None:
            break

        if event.type() == Cocoa.NSEventTypeKeyDown:
            if event.keyCode() == 53:  # ESC key
                raise KeyboardInterrupt

        app.sendEvent_(event)
        app.updateWindows()
