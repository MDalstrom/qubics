from q_engine.ecs.c_bindings import WorldHandle
from q_engine.server.protocol import NetworkServer
from q_engine.server import mk_socket
import numpy as np
from q_generated.components import TestData


def bake(world, net_server):
    comp_id = net_server.register_component_type(TestData.TestData)
    
    entity = world.create_entity([comp_id])
    
    return entity, comp_id


def get_tick():
    world = WorldHandle(chunk_capacity=256)
    net_server = NetworkServer(world)
    transmit = mk_socket(net_server)
    
    entity, comp_id = bake(world, net_server)
    
    frame = [0]
    
    def tick(command_buffer):
        transmit(world)
        
        frame[0] += 1
        if frame[0] % 30 == 0:
            n_entities = 40 + (frame[0] // 30) * 5
            data = np.arange(n_entities * 3, dtype=np.float32).reshape(n_entities, 3)
            data = data * (frame[0] / 100.0)
            
            for chunk in world.query_chunks([comp_id]):
                chunk.set_component_buffer(comp_id, data.tobytes())
            
            update = net_server.build_entity_update(entity, comp_id, data.tobytes())
            transmit.broadcast(update)
            
            print(f"[Server] Broadcasted update: {n_entities} entities, frame {frame[0]}")
    
    return tick

