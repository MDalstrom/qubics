from q_engine.bootstrap import get_config
from q_ecs.c_bindings import mk_world_factory


ecslib = get_config().ecslib
mk_world = mk_world_factory(ecslib)
