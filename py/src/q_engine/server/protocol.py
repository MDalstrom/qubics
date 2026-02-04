from q_engine.ecs.c_bindings import WorldHandle
import flatbuffers
import q_generated.network.ComponentTypeInfo as ComponentTypeInfoMod
import q_generated.network.Handshake as HandshakeMod
import q_generated.network.ComponentUpdate as ComponentUpdateMod
import q_generated.network.EntityUpdate as EntityUpdateMod
import q_generated.network.Message as MessageMod
import q_generated.network.MessagePayload as MessagePayloadMod
import q_generated.network.Batch as BatchMod
from q_generated.network.ComponentTypeInfo import ComponentTypeInfo
from q_generated.network.Handshake import Handshake
from q_generated.network.ComponentUpdate import ComponentUpdate
from q_generated.network.EntityUpdate import EntityUpdate
from q_generated.network.Message import Message
from q_generated.network.MessagePayload import MessagePayload
from q_generated.network.Batch import Batch
import time
import hashlib


def hash_schema(component_name: str) -> int:
    return int(hashlib.md5(component_name.encode()).hexdigest()[:16], 16)


class NetworkServer:
    def __init__(self, world: WorldHandle):
        self.world = world
        self.type_registry = {}
        self.protocol_version = 1
    
    def register_component_type(self, component_class) -> int:
        name = component_class.__name__
        type_id = self.world.register_component_type(component_class)
        self.type_registry[name] = type_id
        return type_id
    
    def build_handshake(self) -> bytes:
        builder = flatbuffers.Builder(1024)
        
        type_infos = []
        for name, type_id in self.type_registry.items():
            name_offset = builder.CreateString(name)
            ComponentTypeInfoMod.ComponentTypeInfoStart(builder)
            ComponentTypeInfoMod.ComponentTypeInfoAddTypeId(builder, type_id)
            ComponentTypeInfoMod.ComponentTypeInfoAddName(builder, name_offset)
            ComponentTypeInfoMod.ComponentTypeInfoAddSchemaHash(builder, hash_schema(name))
            type_infos.append(ComponentTypeInfoMod.ComponentTypeInfoEnd(builder))
        
        HandshakeMod.HandshakeStartComponentTypesVector(builder, len(type_infos))
        for info in reversed(type_infos):
            builder.PrependUOffsetTRelative(info)
        types_vec = builder.EndVector()
        
        HandshakeMod.HandshakeStart(builder)
        HandshakeMod.HandshakeAddComponentTypes(builder, types_vec)
        HandshakeMod.HandshakeAddProtocolVersion(builder, self.protocol_version)
        handshake = HandshakeMod.HandshakeEnd(builder)
        
        MessageMod.MessageStart(builder)
        MessageMod.MessageAddPayloadType(builder, MessagePayload.Handshake)
        MessageMod.MessageAddPayload(builder, handshake)
        MessageMod.MessageAddTimestamp(builder, int(time.time() * 1000))
        msg = MessageMod.MessageEnd(builder)
        
        BatchMod.BatchStartMessagesVector(builder, 1)
        builder.PrependUOffsetTRelative(msg)
        msgs_vec = builder.EndVector()
        
        BatchMod.BatchStart(builder)
        BatchMod.BatchAddMessages(builder, msgs_vec)
        batch = BatchMod.BatchEnd(builder)
        
        builder.Finish(batch)
        return bytes(builder.Output())
    
    def build_entity_update(self, entity_id: int, component_type_id: int, component_data: bytes) -> bytes:
        builder = flatbuffers.Builder(1024)
        
        data_offset = builder.CreateByteVector(component_data)
        
        ComponentUpdateMod.ComponentUpdateStart(builder)
        ComponentUpdateMod.ComponentUpdateAddTypeId(builder, component_type_id)
        ComponentUpdateMod.ComponentUpdateAddData(builder, data_offset)
        comp_update = ComponentUpdateMod.ComponentUpdateEnd(builder)
        
        EntityUpdateMod.EntityUpdateStartComponentUpdatesVector(builder, 1)
        builder.PrependUOffsetTRelative(comp_update)
        updates_vec = builder.EndVector()
        
        EntityUpdateMod.EntityUpdateStart(builder)
        EntityUpdateMod.EntityUpdateAddEntityId(builder, entity_id)
        EntityUpdateMod.EntityUpdateAddComponentUpdates(builder, updates_vec)
        entity_update = EntityUpdateMod.EntityUpdateEnd(builder)
        
        MessageMod.MessageStart(builder)
        MessageMod.MessageAddPayloadType(builder, MessagePayload.EntityUpdate)
        MessageMod.MessageAddPayload(builder, entity_update)
        MessageMod.MessageAddTimestamp(builder, int(time.time() * 1000))
        msg = MessageMod.MessageEnd(builder)
        
        BatchMod.BatchStartMessagesVector(builder, 1)
        builder.PrependUOffsetTRelative(msg)
        msgs_vec = builder.EndVector()
        
        BatchMod.BatchStart(builder)
        BatchMod.BatchAddMessages(builder, msgs_vec)
        batch = BatchMod.BatchEnd(builder)
        
        builder.Finish(batch)
        return bytes(builder.Output())


class NetworkClient:
    def __init__(self, component_classes: dict):
        self.world = WorldHandle()
        self.remote_to_local = {}
        self.component_classes = component_classes
        self.protocol_version = None
    
    def process_handshake(self, handshake: Handshake):
        self.protocol_version = handshake.ProtocolVersion()
        
        for i in range(handshake.ComponentTypesLength()):
            info = handshake.ComponentTypes(i)
            name = info.Name().decode('utf-8')
            remote_id = info.TypeId()
            expected_hash = info.SchemaHash()
            
            if name not in self.component_classes:
                raise ValueError(f"Unknown component type: {name}")
            
            actual_hash = hash_schema(name)
            if actual_hash != expected_hash:
                raise ValueError(f"Schema mismatch for {name}: expected {expected_hash:x}, got {actual_hash:x}")
            
            component_class = self.component_classes[name]
            local_id = self.world.register_component_type(component_class)
            
            self.remote_to_local[remote_id] = local_id
    
    def process_entity_update(self, entity_update: EntityUpdate):
        entity_id = entity_update.EntityId()
        
        for i in range(entity_update.ComponentUpdatesLength()):
            comp_update = entity_update.ComponentUpdates(i)
            remote_type_id = comp_update.TypeId()
            local_type_id = self.remote_to_local[remote_type_id]
            
            data = comp_update.DataAsNumpy().tobytes()
            
            for chunk in self.world.query_chunks([local_type_id]):
                chunk.set_component_buffer(local_type_id, data)
    
    def process_batch(self, batch_data: bytes):
        batch = Batch.GetRootAs(batch_data, 0)
        
        for i in range(batch.MessagesLength()):
            msg = batch.Messages(i)
            payload_type = msg.PayloadType()
            
            if payload_type == MessagePayload.Handshake:
                handshake = Handshake()
                handshake.Init(msg.Payload().Bytes, msg.Payload().Pos)
                self.process_handshake(handshake)
            
            elif payload_type == MessagePayload.EntityUpdate:
                entity_update = EntityUpdate()
                entity_update.Init(msg.Payload().Bytes, msg.Payload().Pos)
                self.process_entity_update(entity_update)
