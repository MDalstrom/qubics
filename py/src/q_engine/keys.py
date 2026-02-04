import Cocoa

_keys_down = set()
mouse_delta = (0, 0)

_SHIFT_KEY_CODE = 56
_CMD_KEY_CODE = 55
_CTRL_KEY_CODE = 59


def up(event):
    _keys_down.discard(event.keyCode())


def down(event):
    _keys_down.add(event.keyCode())


def update_modifier_keys(flags):
    # Shift
    if (flags & Cocoa.NSEventModifierFlagShift) != 0:
        _keys_down.add(_SHIFT_KEY_CODE)
    else:
        _keys_down.discard(_SHIFT_KEY_CODE)
    
    # Command
    if (flags & Cocoa.NSEventModifierFlagCommand) != 0:
        _keys_down.add(_CMD_KEY_CODE)
    else:
        _keys_down.discard(_CMD_KEY_CODE)

    # Control
    if (flags & Cocoa.NSEventModifierFlagControl) != 0:
        _keys_down.add(_CTRL_KEY_CODE)
    else:
        _keys_down.discard(_CTRL_KEY_CODE)


def is_key_down(keyCode):
    return keyCode in _keys_down


def get_mouse_delta():
    global mouse_delta
    temp = mouse_delta
    mouse_delta = (0, 0)
    return temp


def set_mouse_delta(next_delta: tuple[int, int]):
    global mouse_delta
    mouse_delta = next_delta