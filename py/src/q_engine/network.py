from q_ecs.types import World


def mk_system(peer):
    def system(world: World):
        print(world.containers)
    return system
