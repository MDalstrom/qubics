import ctypes
from .shared import TestComponent, TestComponent2
from q_ecs.types import WorldMethods, ComponentDescriptor_p
from q_engine.bootstrap import get_config
from q_ecs.c_bindings import mk_world_factory
from q_ecs.network_bindings import mk_network_factory, ComponentPathResolver


def mk_path_resolver(world_wrapper: WorldMethods) -> ComponentPathResolver:
    _path_cache = {}
    
    def resolver(descriptor_p: ComponentDescriptor_p) -> bytes:
        descriptor_addr = ctypes.cast(descriptor_p, ctypes.c_void_p).value
        
        if descriptor_addr in _path_cache:
            return _path_cache[descriptor_addr]
        
        for component_type, desc in world_wrapper.descriptors_authority.items():
            desc_addr = ctypes.cast(desc, ctypes.c_void_p).value
            if desc_addr == descriptor_addr:
                component_path = f"{component_type.__module__}.{component_type.__name__}"
                result = component_path.encode('utf-8')
                _path_cache[descriptor_addr] = result
                return result
        
        result = b"unknown"
        _path_cache[descriptor_addr] = result
        return result
    
    return ComponentPathResolver(resolver)


def get_tick(config=get_config()):
    ecslib_path = config.ecslib
    world_factory = mk_world_factory(ecslib_path)
    world = world_factory()
    
    network_factory, _ = mk_network_factory(ecslib_path)
    network = network_factory("0.0.0.0", 8080)
    path_resolver = mk_path_resolver(world)
    
    print("Server: Listening on 0.0.0.0:8080")
    print("Server: Waiting for client connection...")
    
    # Accept one client (blocking)
    client_fd = network.accept_client()
    print(f"Server: Client connected (fd={client_fd})")
    
    tick_count = 0

    world.create_entity([TestComponent])
    world.create_entity([TestComponent])
    world.create_entity([TestComponent])
    world.create_entity([TestComponent])
    world.create_entity([TestComponent])

    def tick(**kwargs):
        nonlocal tick_count
        tick_count += 1
        
        # Send world to client
        success = network.send_world(client_fd, world.handle, path_resolver)
        if success:
            print(f"Tick {tick_count}: Sent world state to client ({world.handle})")
        else:
            print(f"Tick {tick_count}: Failed to send world state")

    return tick

