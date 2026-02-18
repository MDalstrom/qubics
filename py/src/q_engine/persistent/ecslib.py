from q_ecs.c_bindings import mk_world_factory
from q_engine.bootstrap import get_config


mk_world = mk_world_factory(get_config().ecslib)
