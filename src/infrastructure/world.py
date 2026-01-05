from dataclasses import dataclass, field


@dataclass
class EntityRef:
    index: int
    generation: int = 0


@dataclass
class World:
    entities: list = field(default_factory=list)
    _generation: int = field(default=0, init=False)
    
    def add(self, entity):
        index = len(self.entities)
        self.entities.append(entity)
        return EntityRef(index, self._generation)
    
    def validate(self, ref: EntityRef):
        return ref.generation == self._generation and 0 <= ref.index < len(self.entities)
    
    def get(self, ref: EntityRef):
        if not self.validate(ref):
            return None
        return self.entities[ref.index]
    
    def rebuild_indices(self):
        self._generation += 1
    
    def __iter__(self):
        return iter(self.entities)


def create_world():
    return World()
