#import "ECSWorldManager.h"
#import <dlfcn.h>

typedef World* (*world_create_fn)(void);
typedef void (*world_destroy_fn)(World*);
typedef Entity (*entity_create_fn)(World*, Archetype);

@implementation ECSWorldManager {
    void *_libHandle;
    world_create_fn _world_create;
    world_destroy_fn _world_destroy;
    entity_create_fn _entity_create;
}

- (instancetype)initWithLibraryPath:(NSString *)path {
    self = [super init];
    if (self) {
        _libHandle = dlopen([path UTF8String], RTLD_NOW);
        if (!_libHandle) {
            NSLog(@"Failed to load ECS library: %s", dlerror());
            return nil;
        }
        
        _world_create = (world_create_fn)dlsym(_libHandle, "world_create");
        _world_destroy = (world_destroy_fn)dlsym(_libHandle, "world_destroy");
        _entity_create = (entity_create_fn)dlsym(_libHandle, "entity_create");
        
        if (!_world_create || !_world_destroy || !_entity_create) {
            NSLog(@"Failed to load ECS functions");
            dlclose(_libHandle);
            return nil;
        }
        
        _world = _world_create();
    }
    return self;
}

- (void)createEntity:(Archetype)archetype {
    if (_world && _entity_create) {
        _entity_create(_world, archetype);
    }
}

- (ChunkContainer *)getContainer:(NSUInteger)index {
    if (_world && index < _world->containers_count) {
        return &_world->containers[index];
    }
    return NULL;
}

- (NSUInteger)containerCount {
    return _world ? _world->containers_count : 0;
}

- (void)dealloc {
    if (_world && _world_destroy) {
        _world_destroy(_world);
    }
    if (_libHandle) {
        dlclose(_libHandle);
    }
}

@end
