#import <Metal/Metal.h>
#import <MetalKit/MetalKit.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "api/contract.h"
#include "backend-metal/contract.h"
#include "mesh2d.h"

static uint32_t component_id(const char *s) {
    uint32_t hash = 2166136261u;
    for (; *s; s++) hash = hash * 16777619u ^ (uint8_t)*s;
    return hash;
}

static id<MTLRenderPipelineState> g_pipeline = nil;
static RegistryApi g_api;

static ComponentDescriptor g_transform_comp = NULL;
static ComponentDescriptor g_viewport_comp  = NULL;
static ComponentDescriptor g_mesh_comp      = NULL;

static void mat4_identity(float *m) {
    memset(m, 0, 64);
    m[0] = m[5] = m[10] = m[15] = 1.0f;
}

static void mat4_mul(float *out, const float *a, const float *b) {
    for (int col = 0; col < 4; col++)
        for (int row = 0; row < 4; row++) {
            float s = 0;
            for (int k = 0; k < 4; k++)
                s += a[k*4+row] * b[col*4+k];
            out[col*4+row] = s;
        }
}

static void ortho(float *m, float l, float r, float b, float t, float n, float f) {
    memset(m, 0, 64);
    m[0]  =  2.0f / (r - l);
    m[5]  =  2.0f / (t - b);
    m[10] = -2.0f / (f - n);
    m[12] = -(r + l) / (r - l);
    m[13] = -(t + b) / (t - b);
    m[14] = -(f + n) / (f - n);
    m[15] =  1.0f;
}

static void setup_pipeline(id<MTLDevice> device, MTKView *view) {
    const char *build = getenv("QUBICS_PATH");
    if (!build) { fprintf(stderr, "[mesh2d] QUBICS_PATH not set\n"); return; }

    char path[1024];
    snprintf(path, sizeof(path), "%s/mesh2d/mesh2d.metallib", build);

    NSError *err = nil;
    id<MTLLibrary> lib = [device newLibraryWithURL:[NSURL fileURLWithPath:@(path)] error:&err];
    if (!lib) {
        fprintf(stderr, "[mesh2d] failed to load %s: %s\n", path,
                [[err localizedDescription] UTF8String]);
        return;
    }

    MTLRenderPipelineDescriptor *desc = [[MTLRenderPipelineDescriptor alloc] init];
    desc.vertexFunction   = [lib newFunctionWithName:@"vert_main"];
    desc.fragmentFunction = [lib newFunctionWithName:@"frag_main"];
    desc.colorAttachments[0].pixelFormat = view.colorPixelFormat;

    g_pipeline = [device newRenderPipelineStateWithDescriptor:desc error:&err];
    if (!g_pipeline)
        fprintf(stderr, "[mesh2d] pipeline error: %s\n", [[err localizedDescription] UTF8String]);
}

static void mesh2d_render(WorldApi *world, void *ctx_ptr) {
    if (!ctx_ptr) return;

    if (!g_transform_comp) g_transform_comp = g_api.find(component_id("Transform"));
    if (!g_viewport_comp)  g_viewport_comp  = g_api.find(component_id("Viewport"));
    if (!g_mesh_comp)      g_mesh_comp      = g_api.find(component_id("Mesh2DShared"));
    if (!g_transform_comp || !g_viewport_comp || !g_mesh_comp) return;

    RenderContext *rc = (RenderContext *)ctx_ptr;
    MTKView *view = (__bridge MTKView *)rc->mtkView;
    id<MTLDevice> dev = (__bridge id<MTLDevice>)rc->device;
    id<MTLCommandQueue> queue = (__bridge id<MTLCommandQueue>)rc->commandQueue;

    if (!g_pipeline) {
        setup_pipeline(dev, view);
        if (!g_pipeline) return;
    }

    float vp[16];
    mat4_identity(vp);

    ComponentDescriptor cam_generic[] = {g_viewport_comp, g_transform_comp};
    Archetype cam_arch = {.generic = cam_generic, .generic_count = 2};
    QueryResult cam_r = world->query_at_least(cam_arch);
    for (size_t i = 0; i < cam_r.count; i++) {
        if (cam_r.counts[i] == 0) continue;
        void **bufs = (void **)cam_r.buffers[i];
        float proj[16];
        ortho(proj,
              ((Viewport *)bufs[0])[0].left,  ((Viewport *)bufs[0])[0].right,
              ((Viewport *)bufs[0])[0].bottom, ((Viewport *)bufs[0])[0].top,
              ((Viewport *)bufs[0])[0].near_z, ((Viewport *)bufs[0])[0].far_z);
        mat4_mul(vp, proj, ((Transform *)bufs[1])[0].matrix);
        break;
    }

    MTLRenderPassDescriptor *rpd = view.currentRenderPassDescriptor;
    if (!rpd) return;
    rpd.colorAttachments[0].clearColor = MTLClearColorMake(0.08, 0.08, 0.12, 1.0);
    rpd.colorAttachments[0].loadAction = MTLLoadActionClear;

    id<MTLCommandBuffer> cmdbuf = [queue commandBuffer];
    id<MTLRenderCommandEncoder> enc = [cmdbuf renderCommandEncoderWithDescriptor:rpd];
    [enc setRenderPipelineState:g_pipeline];
    [enc setVertexBytes:vp length:sizeof(vp) atIndex:2];

    Mesh2DShared *mesh = (Mesh2DShared *)world->get_shared_buffer(g_mesh_comp);
    if (!mesh) {
        [enc endEncoding];
        [cmdbuf commit];
        return;
    }

    size_t page = (size_t)getpagesize();
    size_t vert_bytes = mesh->vertex_count * 2 * sizeof(float);
    size_t vert_aligned = (vert_bytes + page - 1) & ~(page - 1);
    id<MTLBuffer> vtx = [dev newBufferWithBytesNoCopy:mesh->vertex_buffer
                                               length:vert_aligned
                                              options:MTLResourceStorageModeShared
                                          deallocator:nil];
    [enc setVertexBuffer:vtx offset:0 atIndex:0];
    [enc setFragmentBytes:mesh->color length:sizeof(mesh->color) atIndex:0];

    ComponentDescriptor mesh_generic[] = {g_transform_comp};
    Archetype mesh_arch = {
        .generic = mesh_generic, .generic_count = 1,
        .shared  = &g_mesh_comp, .shared_count  = 1,
    };
    QueryResult mesh_r = world->query_at_least(mesh_arch);
    for (size_t i = 0; i < mesh_r.count; i++) {
        if (mesh_r.counts[i] == 0) continue;
        void **bufs = (void **)mesh_r.buffers[i];
        size_t inst_bytes = sizeof(Transform) * mesh_r.counts[i];
        size_t inst_aligned = (inst_bytes + page - 1) & ~(page - 1);
        id<MTLBuffer> inst = [dev newBufferWithBytesNoCopy:bufs[0]
                                                    length:inst_aligned
                                                   options:MTLResourceStorageModeShared
                                               deallocator:nil];
        [enc setVertexBuffer:inst offset:0 atIndex:1];
        [enc drawPrimitives:MTLPrimitiveTypeTriangle
                vertexStart:0
                vertexCount:mesh->vertex_count
              instanceCount:(NSUInteger)mesh_r.counts[i]];
    }

    [enc endEncoding];
    [cmdbuf presentDrawable:view.currentDrawable];
    [cmdbuf commit];
}

PluginState qubics_plugin(RegistryApi api) {
    g_api            = api;
    g_transform_comp = NULL;
    g_viewport_comp  = NULL;
    g_mesh_comp      = NULL;
    g_pipeline       = nil;

    SystemDescriptor *render_descs = malloc(sizeof(SystemDescriptor));
    render_descs[0] = (SystemDescriptor){
        .fn     = (void (*)(void *))mesh2d_render,
        .reads  = {NULL, 0, NULL, 0},
        .writes = {NULL, 0, NULL, 0},
    };

    return (PluginState){
        .render       = render_descs,
        .render_count = 1,
    };
}
