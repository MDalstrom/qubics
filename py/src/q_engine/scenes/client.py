from q_engine.network.network import Network
import curses
import ctypes

from bridge.types import Component, World
from bridge.c_bindings import mk_world_factory
from q_engine.bootstrap import get_config


class Position(Component):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]


class Velocity(Component):
    _fields_ = [("dx", ctypes.c_float), ("dy", ctypes.c_float), ("dz", ctypes.c_float)]


ALL_COMPONENTS = [Position, Velocity]


def render_header(win, line, containers_count):
    win.addstr(line, 0, f"  {containers_count} containers")
    return line + 1


def render_entity_indices(win, line, col_start, entity_count, col_width=8):
    for i in range(entity_count):
        win.addstr(line, col_start + i * col_width, str(i))
    return line + 1


def render_chunk_container_header(win, line, container_idx, chunks_count):
    win.addstr(line, 0, f"# {container_idx} ({chunks_count} ch.):")
    return line + 1


def render_component_header(win, line, component_name):
    win.addstr(line, 0, f"  [{component_name}]")
    return line + 1


def render_component_field(win, line, field_name, values, col_start=20, col_width=8):
    win.addstr(line, 0, f"    {field_name}:")
    for i, value in enumerate(values):
        value_str = f"{value:.3f}" if isinstance(value, float) else str(value)
        win.addstr(line, col_start + i * col_width, value_str)
    return line + 1


def render_container(
    win, line, world_wrapper, container_idx, container, col_start=20, col_width=8
):
    line = render_chunk_container_header(
        win, line, container_idx, container.chunks_count
    )

    max_entities = 0
    for chunk_idx in range(container.chunks_count):
        chunk = container.chunks[chunk_idx]
        max_entities = max(max_entities, chunk.entities_count)

    line = render_entity_indices(win, line, col_start, max_entities, col_width)

    archetype = container.archetype
    for comp_idx in range(archetype.length):
        descriptor = archetype.descriptors[comp_idx]
        component_type = None
        for comp in ALL_COMPONENTS:
            if ctypes.sizeof(comp) == descriptor.contents.stride:
                component_type = comp
                break
        if component_type is None:
            continue
        component_name = component_type.__name__
        line = render_component_header(win, line, component_name)

        for field_name, field_type in component_type._fields_:
            values = []
            for chunk_idx in range(container.chunks_count):
                chunk = container.chunks[chunk_idx]
                if chunk.entities_count > 0:
                    buffer = ctypes.cast(
                        chunk.buffers[comp_idx],
                        ctypes.POINTER(component_type * chunk.entities_count),
                    )
                    for entity_idx in range(chunk.entities_count):
                        values.append(getattr(buffer.contents[entity_idx], field_name))
            line = render_component_field(
                win, line, field_name, values, col_start, col_width
            )

    return line


def render_world(win, world_wrapper, world_h):
    line = 0
    n = world_h.containers_count
    line = render_header(win, line, n)

    for container_idx in range(n):
        container = world_h.containers[container_idx]
        line = render_container(win, line, world_wrapper, container_idx, container)

    return line


def get_tick(config=get_config()):
    world_handle = mk_world_factory(config.ecslib)()
    
    for comp in ALL_COMPONENTS:
        world_handle._get_descriptor(comp)

    net = Network(world_handle, listen_port=18489)
    
    import threading
    import time
    connect_thread = threading.Thread(target=lambda: net.connect("localhost", 18488), daemon=True)
    connect_thread.start()
    
    time.sleep(0.5)
    
    recv_thread = threading.Thread(target=lambda: recv_loop(net), daemon=True)
    recv_thread.start()

    cursor = 0

    def tick(win, key):
        nonlocal cursor

        world_h = World.from_address(world_handle.handle)
        
        line = render_world(win, world_handle, world_h)

        if key == curses.KEY_UP:
            cursor -= 1
        elif key == curses.KEY_DOWN:
            cursor += 1
        max_y, max_x = win.getmaxyx()
        max_y = min(line - 1, max_y)
        cursor = max(0, min(max_y, cursor))
        win.addstr(cursor, 0, ">")

    return tick

def recv_loop(net):
    import time
    while True:
        try:
            net.recv_and_update_world()
        except Exception:
            pass
        time.sleep(0.016)
