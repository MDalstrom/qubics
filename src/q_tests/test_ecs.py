import unittest
from src.q_engine.ecs.components import World, Component, Removed, Count, CommandBuffer, DeferredEntity, Entity


class TestECS(unittest.TestCase):
    def test_entity_creation(self):
        world = World()
        entity = world.create_entity()
        self.assertIsNotNone(entity)
        self.assertEqual(world.archetypes[0].components[Count].count, 1)
        self.assertEqual(entity.archetype.types, {Removed, Count})

    def test_add_component_to_entity(self):
        world = World()
        entity = world.create_entity()
        initial_archetype = entity.archetype
        old_index = entity.index

        class MyComponent(Component):
            def __init__(self): pass
            def add(self, i: int, size: int = 1): pass

        world.move_entity(entity, {MyComponent})

        self.assertNotEqual(initial_archetype, entity.archetype)
        self.assertIn(MyComponent, entity.archetype.types)
        self.assertEqual(entity.archetype.types, {MyComponent, Removed, Count})

        removals: Removed = initial_archetype.components[Removed]
        self.assertTrue(removals[old_index])

    def test_remove_component_from_entity(self):
        world = World()

        class MyComponent(Component):
            def __init__(self): pass
            def add(self, i: int, size: int = 1): pass

        entity = world.create_entity()
        world.move_entity(entity, {MyComponent})
        self.assertIn(MyComponent, entity.archetype.types)
        archetype_with_component = entity.archetype
        old_index = entity.index

        world.move_entity(entity, set())

        self.assertNotEqual(archetype_with_component, entity.archetype)
        self.assertNotIn(MyComponent, entity.archetype.types)
        self.assertEqual(entity.archetype.types, {Removed, Count})

        removals: Removed = archetype_with_component.components[Removed]
        self.assertTrue(removals[old_index])

    def test_command_buffer_deferred_entity_and_add_component(self):
        world = World()
        cmd = CommandBuffer()
        deferred_entity = cmd.create_entity()

        class ComponentA(Component):
            def __init__(self): pass
            def add(self, i: int, size: int = 1): pass

        cmd.add_component(deferred_entity, ComponentA)
        created_entities = cmd.playback(world)
        
        self.assertEqual(len(created_entities), 1)
        entity = created_entities[0]
        self.assertIn(ComponentA, entity.archetype.types)

    def test_command_buffer_remove_component(self):
        world = World()

        class ComponentB(Component):
            def __init__(self): pass
            def add(self, i: int, size: int = 1): pass

        entity = world.create_entity()
        world.move_entity(entity, {ComponentB})
        self.assertIn(ComponentB, entity.archetype.types)

        cmd = CommandBuffer()
        cmd.remove_component(entity, ComponentB)
        cmd.playback(world)

        self.assertNotIn(ComponentB, entity.archetype.types)

    def test_command_buffer_set_component(self):
        world = World()

        class MyComponent(Component):
            def __init__(self):
                self.value = 0
            def add(self, i: int, size: int = 1): pass

        entity = world.create_entity()
        world.move_entity(entity, {MyComponent})

        cmd = CommandBuffer()
        
        def set_my_component_value(e_in_fn, component_in_fn: MyComponent): 
            component_in_fn.value = 42

        cmd.set_component(entity, MyComponent, set_my_component_value)
        cmd.playback(world)

        retrieved_component: MyComponent = entity.archetype.components[MyComponent]
        self.assertEqual(retrieved_component.value, 42)

if __name__ == '__main__':
    unittest.main()