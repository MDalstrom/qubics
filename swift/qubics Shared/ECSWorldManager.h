#import "../../c/ecs.h"
#import <Metal/Metal.h>

@interface ECSWorldManager : NSObject

@property (nonatomic, assign) World *world;

- (instancetype)initWithLibraryPath:(NSString *)path;
- (void)createEntity:(Archetype)archetype;
- (ChunkContainer *)getContainer:(NSUInteger)index;
- (NSUInteger)containerCount;

@end
