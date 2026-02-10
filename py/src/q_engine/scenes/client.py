import ctypes
from .shared import TestComponent, TestComponent2
from q_ecs.types import ComponentDescriptor_p
from q_engine.bootstrap import get_config
from q_ecs.c_bindings import mk_world_factory
from q_ecs.network_bindings import mk_network_factory, ComponentPathLookup


def mk_path_lookup(component_registry: dict[str, type]) -> ComponentPathLookup:
    """Create a lookup function that maps component paths to descriptors."""
    descriptor_cache = {}
    lib = ctypes.CDLL(get_config().ecslib)
    lib.component_describe.argtypes = [ctypes.c_size_t]
    lib.component_describe.restype = ctypes.c_void_p
    
    def lookup(path_bytes: bytes) -> ctypes.c_void_p:
        path = path_bytes.decode('utf-8')
        
        if path in descriptor_cache:
            return descriptor_cache[path]
        
        if path in component_registry:
            component_type = component_registry[path]
            stride = ctypes.sizeof(component_type)
            descriptor = lib.component_describe(stride)
            descriptor_cache[path] = descriptor
            return descriptor
        
        return None
    
    return ComponentPathLookup(lookup)


def get_tick(config=get_config()):
    ecslib_path = config.ecslib
    world_factory = mk_world_factory(ecslib_path)
    world = world_factory()
    
    component_registry = {
        f"{TestComponent.__module__}.{TestComponent.__name__}": TestComponent,
        f"{TestComponent2.__module__}.{TestComponent2.__name__}": TestComponent2,
    }
    
    path_lookup = mk_path_lookup(component_registry)
    
    _, NetworkClient = mk_network_factory(ecslib_path)
    
    # For TUI mode, we'll connect in a non-blocking way
    client = None
    connected = False
    tick_count = 0
    
    def tick(**kwargs):
        nonlocal client, connected, tick_count
        tick_count += 1
        
        # Try to connect on first tick
        if not connected and client is None:
            try:
                print("Client: Attempting to connect to server at 127.0.0.1:8080...")
                client = NetworkClient("127.0.0.1", 8080)
                connected = True
                print("Client: Connected to server!")
            except Exception as e:
                print(f"Client: Connection failed: {e}")
                return
        
        if not connected:
            return
        
        # Receive world state
        try:
            new_world_handle = client.receive_world(path_lookup)
            
            if new_world_handle:
                world.handle = new_world_handle
                
                # If running in TUI mode, update the app
                if config.api == "tui":
                    from q_engine.persistent.tui import state
                    if hasattr(state, 'app') and state.app:
                        state.app.update_world_view(world.handle)
                else:
                    # Print world state for non-TUI mode
                    from q_ecs.types import World
                    world_struct = World.from_address(world.handle)
                    print(f"\nTick {tick_count}: Received world state")
                    print(f"  Containers: {world_struct.containers_count}")
                    
                    for i in range(world_struct.containers_count):
                        container = world_struct.containers[i]
                        total_entities = sum(container.chunks[j].entities_count 
                                           for j in range(container.chunks_count))
                        print(f"  Container {i}:")
                        print(f"    Archetype components: {container.archetype.length}")
                        print(f"    Total entities: {total_entities}")
                        print(f"    Chunks: {container.chunks_count}")
        except Exception as e:
            print(f"Tick {tick_count}: Error receiving world state: {e}")
    
    return tick
