#import "render_3d.h"
#import <dlfcn.h>

static id<MTLDevice> _device;
static MTKView *_view;
static id<MTLRenderPipelineState> _pipeline;
static id<MTLBuffer> _vertexBuffer;
static id<MTLBuffer> _colorBuffer;
static simd_float4x4 _viewProjectionMatrix;
static float _rotation = 0.0f;

static void render_3d_tick(World *world, void *commandBufferPtr) {
    id<MTLCommandBuffer> commandBuffer = (__bridge id<MTLCommandBuffer>)commandBufferPtr;
    MTLRenderPassDescriptor *rpd = _view.currentRenderPassDescriptor;
    if (!rpd) return;
    
    id<MTLRenderCommandEncoder> encoder = [commandBuffer renderCommandEncoderWithDescriptor:rpd];
    [encoder setRenderPipelineState:_pipeline];
    
    id<MTLBuffer> vpBuffer = [_device newBufferWithBytes:&_viewProjectionMatrix
                                                   length:sizeof(simd_float4x4)
                                                  options:MTLResourceStorageModeManaged];
    [encoder setVertexBuffer:vpBuffer offset:0 atIndex:3];
    [encoder setVertexBuffer:_vertexBuffer offset:0 atIndex:0];
    [encoder setVertexBuffer:_colorBuffer offset:0 atIndex:1];
    
    simd_float3 axis = simd_normalize(simd_make_float3(1.0f, 1.0f, 0.0f));
    float c = cosf(_rotation);
    float s = sinf(_rotation);
    float t = 1.0f - c;
    float x = axis.x, y = axis.y, z = axis.z;
    
    simd_float4x4 modelMatrix = {
        .columns[0] = simd_make_float4(t*x*x + c, t*x*y + z*s, t*x*z - y*s, 0),
        .columns[1] = simd_make_float4(t*x*y - z*s, t*y*y + c, t*y*z + x*s, 0),
        .columns[2] = simd_make_float4(t*x*z + y*s, t*y*z - x*s, t*z*z + c, 0),
        .columns[3] = simd_make_float4(0, 0, 0, 1)
    };
    
    id<MTLBuffer> instanceBuffer = [_device newBufferWithBytes:&modelMatrix
                                                        length:sizeof(simd_float4x4)
                                                       options:MTLResourceStorageModeManaged];
    [encoder setVertexBuffer:instanceBuffer offset:0 atIndex:2];
    
    [encoder drawPrimitives:MTLPrimitiveTypeTriangle vertexStart:0 vertexCount:36 instanceCount:1];
    [encoder endEncoding];
    
    _rotation += 0.01f;
}

RenderFunction render_3d_create(const char *metalbootPath, 
                                  const char *shadersPath,
                                  const char *shaderNames) {
    void *metalboot = dlopen(metalbootPath, RTLD_LAZY);
    if (!metalboot) return NULL;
    
    void* (*get_device)(void) = dlsym(metalboot, "metal_get_device");
    void* (*get_view)(void) = dlsym(metalboot, "metal_get_view");
    void* (*load_library)(const char*) = dlsym(metalboot, "metal_load_library");
    
    if (!get_device || !get_view || !load_library) return NULL;
    
    void *devicePtr = get_device();
    void *viewPtr = get_view();
    void *libraryPtr = load_library(shadersPath);
    
    if (!devicePtr || !viewPtr || !libraryPtr) return NULL;
    
    _device = (__bridge id<MTLDevice>)devicePtr;
    _view = (__bridge MTKView *)viewPtr;
    id<MTLLibrary> library = (__bridge id<MTLLibrary>)libraryPtr;
    
    MTLRenderPipelineDescriptor *desc = [[MTLRenderPipelineDescriptor alloc] init];
    desc.vertexFunction = [library newFunctionWithName:@"vertex_main"];
    desc.fragmentFunction = [library newFunctionWithName:@"fragment_main"];
    desc.colorAttachments[0].pixelFormat = _view.colorPixelFormat;
    
    NSError *error;
    _pipeline = [_device newRenderPipelineStateWithDescriptor:desc error:&error];
    if (!_pipeline) return NULL;
    
    simd_float3 cameraPos = simd_make_float3(0.0f, 0.0f, -8.0f);
    simd_float4x4 viewMatrix = matrix_identity_float4x4;
    viewMatrix.columns[3] = simd_make_float4(cameraPos.x, cameraPos.y, cameraPos.z, 1.0f);
    viewMatrix = simd_inverse(viewMatrix);
    
    float aspect = 1.0f;
    float fov = 65.0f * M_PI / 180.0f;
    float near = 0.1f;
    float far = 100.0f;
    float f = 1.0f / tanf(fov * 0.5f);
    
    simd_float4x4 projection = {
        .columns[0] = simd_make_float4(f / aspect, 0, 0, 0),
        .columns[1] = simd_make_float4(0, f, 0, 0),
        .columns[2] = simd_make_float4(0, 0, far / (far - near), 1),
        .columns[3] = simd_make_float4(0, 0, -near * far / (far - near), 0)
    };
    
    _viewProjectionMatrix = simd_mul(viewMatrix, projection);
    
    float vertices[] = {
        -1.0f, -1.0f, -1.0f, 1.0f,  1.0f, -1.0f, -1.0f, 1.0f,  1.0f,  1.0f, -1.0f, 1.0f,
        -1.0f, -1.0f, -1.0f, 1.0f,  1.0f,  1.0f, -1.0f, 1.0f, -1.0f,  1.0f, -1.0f, 1.0f,
        -1.0f, -1.0f,  1.0f, 1.0f,  1.0f,  1.0f,  1.0f, 1.0f,  1.0f, -1.0f,  1.0f, 1.0f,
        -1.0f, -1.0f,  1.0f, 1.0f, -1.0f,  1.0f,  1.0f, 1.0f,  1.0f,  1.0f,  1.0f, 1.0f,
        -1.0f, -1.0f, -1.0f, 1.0f, -1.0f,  1.0f,  1.0f, 1.0f, -1.0f, -1.0f,  1.0f, 1.0f,
        -1.0f, -1.0f, -1.0f, 1.0f, -1.0f,  1.0f, -1.0f, 1.0f, -1.0f,  1.0f,  1.0f, 1.0f,
         1.0f, -1.0f, -1.0f, 1.0f,  1.0f, -1.0f,  1.0f, 1.0f,  1.0f,  1.0f,  1.0f, 1.0f,
         1.0f, -1.0f, -1.0f, 1.0f,  1.0f,  1.0f,  1.0f, 1.0f,  1.0f,  1.0f, -1.0f, 1.0f,
        -1.0f, -1.0f, -1.0f, 1.0f, -1.0f, -1.0f,  1.0f, 1.0f,  1.0f, -1.0f,  1.0f, 1.0f,
        -1.0f, -1.0f, -1.0f, 1.0f,  1.0f, -1.0f,  1.0f, 1.0f,  1.0f, -1.0f, -1.0f, 1.0f,
        -1.0f,  1.0f, -1.0f, 1.0f,  1.0f,  1.0f,  1.0f, 1.0f, -1.0f,  1.0f,  1.0f, 1.0f,
        -1.0f,  1.0f, -1.0f, 1.0f,  1.0f,  1.0f, -1.0f, 1.0f,  1.0f,  1.0f,  1.0f, 1.0f
    };
    
    float colors[] = {
        0.0f, 0.0f, 1.0f, 1.0f,  0.0f, 0.0f, 1.0f, 1.0f,  0.0f, 0.0f, 1.0f, 1.0f,
        0.0f, 0.0f, 1.0f, 1.0f,  0.0f, 0.0f, 1.0f, 1.0f,  0.0f, 0.0f, 1.0f, 1.0f,
        0.0f, 1.0f, 0.0f, 1.0f,  0.0f, 1.0f, 0.0f, 1.0f,  0.0f, 1.0f, 0.0f, 1.0f,
        0.0f, 1.0f, 0.0f, 1.0f,  0.0f, 1.0f, 0.0f, 1.0f,  0.0f, 1.0f, 0.0f, 1.0f,
        1.0f, 0.0f, 0.0f, 1.0f,  1.0f, 0.0f, 0.0f, 1.0f,  1.0f, 0.0f, 0.0f, 1.0f,
        1.0f, 0.0f, 0.0f, 1.0f,  1.0f, 0.0f, 0.0f, 1.0f,  1.0f, 0.0f, 0.0f, 1.0f,
        1.0f, 1.0f, 0.0f, 1.0f,  1.0f, 1.0f, 0.0f, 1.0f,  1.0f, 1.0f, 0.0f, 1.0f,
        1.0f, 1.0f, 0.0f, 1.0f,  1.0f, 1.0f, 0.0f, 1.0f,  1.0f, 1.0f, 0.0f, 1.0f,
        1.0f, 0.0f, 1.0f, 1.0f,  1.0f, 0.0f, 1.0f, 1.0f,  1.0f, 0.0f, 1.0f, 1.0f,
        1.0f, 0.0f, 1.0f, 1.0f,  1.0f, 0.0f, 1.0f, 1.0f,  1.0f, 0.0f, 1.0f, 1.0f,
        0.0f, 1.0f, 1.0f, 1.0f,  0.0f, 1.0f, 1.0f, 1.0f,  0.0f, 1.0f, 1.0f, 1.0f,
        0.0f, 1.0f, 1.0f, 1.0f,  0.0f, 1.0f, 1.0f, 1.0f,  0.0f, 1.0f, 1.0f, 1.0f
    };
    
    _vertexBuffer = [_device newBufferWithBytes:vertices
                                         length:sizeof(vertices)
                                        options:MTLResourceStorageModeManaged];
    
    _colorBuffer = [_device newBufferWithBytes:colors
                                        length:sizeof(colors)
                                       options:MTLResourceStorageModeManaged];
    
    return render_3d_tick;
}
