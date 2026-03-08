#import "ecs.h"
#import <Metal/Metal.h>
#import <MetalKit/MetalKit.h>
#import <simd/simd.h>

typedef void (*RenderFunction)(World *world, void *commandBuffer);

RenderFunction render_3d_create(const char *metalbootPath, 
                                  const char *shadersPath,
                                  const char *shaderNames);
