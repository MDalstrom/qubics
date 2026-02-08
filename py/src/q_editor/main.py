from textual.app import App, ComposeResult
from textual.widgets import Tree

class EditorApp(App):
    def compose(self) -> ComposeResult:
        tree = Tree("Root")
        tree.root.expand()
        yield tree

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        root_node = tree.root

        components_section = root_node.add("Components")
        entities_section = root_node.add("Entities")

        components_section.add_leaf("Transform")
        components_section.add_leaf("Renderable")
        components_section.add_leaf("PhysicsBody")
        
        entity1_node = entities_section.add("Player")
        entity1_node.add_leaf("Position: (0, 0, 0)")
        entity1_node.add_leaf("Velocity: (1, 0, 0)")
        
        entity2_node = entities_section.add("Enemy")
        entity2_node.add_leaf("Sprite: 'enemy.png'")
        entity2_node.add_leaf("Health: 100")
        entity2_node.add_leaf("Attack: 10")

        components_section.expand()
        entities_section.expand()

EditorApp().run()
