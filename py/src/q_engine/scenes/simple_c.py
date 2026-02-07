from q_engine.bootstrap import get_config
from q_engine.persistent.metal import state as metal_state

from q_engine.ecs.c_bindings import WorldHandle, TestComponent


def mk_system(world: WorldHandle, entity: int):
    def system():
        test_component = world.get_component(entity, TestComponent)
        if test_component:
            print(f"TestComponent value: {test_component.value}")

    return system

def get_tick(state = metal_state, config = get_config()):
    world = WorldHandle(capacity=256)
    world.register_component(TestComponent)
    
    e = world.create_entity([TestComponent])
    
    test_component_instance = world.get_component(e, TestComponent)
    if test_component_instance:
        test_component_instance.value = 123

    system = mk_system(world, e)

    def tick(**kwargs):
        system()
        
    return tick
