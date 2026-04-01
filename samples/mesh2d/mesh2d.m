#import <Metal/Metal.h>
#import <MetalKit/MetalKit.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#include "backend-contracts/contract.h"
#include "backend-metal/contract.h"
#include "ecs/api.h"
#include "mesh2d.h"

// ---------------------------------------------------------------------------
// Global state (reset on each qubics_plugin call / hot-reload)
// ---------------------------------------------------------------------------

static ComponentDescriptor       *g_mesh2d_desc     = NULL;
static id<MTLRenderPipelineState> g_pipeline         = nil;
static bool                       g_entities_created = false;

// ---------------------------------------------------------------------------
// Shaders
// ---------------------------------------------------------------------------

static NSString *kShaderSrc = @""
    "#include <metal_stdlib>\n"
    "using namespace metal;\n"
    "\n"
    "vertex float4 vert_main(uint vid           [[vertex_id]],\n"
    "                        constant float2 *v [[buffer(0)]]) {\n"
    "    return float4(v[vid], 0.0, 1.0);\n"
    "}\n"
    "\n"
    "fragment float4 frag_main(float4             pos [[stage_in]],\n"
    "                          constant float4 &color [[buffer(0)]]) {\n"
    "    return color;\n"
    "}\n";

static void setup_pipeline(id<MTLDevice> device, MTKView *view) {
    NSError *err = nil;
    id<MTLLibrary> lib = [device newLibraryWithSource:kShaderSrc
                                              options:nil
                                                error:&err];
    if (!lib) {
        fprintf(stderr, "[mesh2d] shader compile error: %s\n",
                [[err localizedDescription] UTF8String]);
        return;
    }

    MTLRenderPipelineDescriptor *desc = [[MTLRenderPipelineDescriptor alloc] init];
    desc.vertexFunction   = [lib newFunctionWithName:@"vert_main"];
    desc.fragmentFunction = [lib newFunctionWithName:@"frag_main"];
    desc.colorAttachments[0].pixelFormat = view.colorPixelFormat;

    g_pipeline = [device newRenderPipelineStateWithDescriptor:desc error:&err];
    if (!g_pipeline) {
        fprintf(stderr, "[mesh2d] pipeline state error: %s\n",
                [[err localizedDescription] UTF8String]);
    }
}

// ---------------------------------------------------------------------------
// System
// ---------------------------------------------------------------------------

static void mesh2d_system(WorldApi *world_ptr, void *ctx_ptr) {
    if (!ctx_ptr || !g_mesh2d_desc) return;

    RenderContext *rc   = (RenderContext *)ctx_ptr;

    MTKView            *view  = (__bridge MTKView *)rc->mtkView;
    id<MTLDevice>       dev   = (__bridge id<MTLDevice>)rc->device;
    id<MTLCommandQueue> queue = (__bridge id<MTLCommandQueue>)rc->commandQueue;

    if (!g_pipeline) {
        setup_pipeline(dev, view);
        if (!g_pipeline) return;
    }

    // Seed demo entities once per load cycle
    if (!g_entities_created) {
        g_entities_created = true;

        ComponentDescriptor *desc_arr[] = { g_mesh2d_desc };
        Archetype arch = { 1, desc_arr };

        // Blue triangle (NDC coords)
        Entity tri = world_ptr->create_entity(arch);
        Mesh2D *t = &((Mesh2D *)tri.chunk->buffers[0])[tri.idx];
        t->point_count = 3;
        t->points[0] = (Point2D){  0.0f,  0.5f };
        t->points[1] = (Point2D){ -0.5f, -0.5f };
        t->points[2] = (Point2D){  0.5f, -0.5f };
        t->r = 0.2f; t->g = 0.6f; t->b = 1.0f; t->a = 1.0f;

        // Orange quad (4 points — triangle fan renders 2 triangles)
        Entity quad = world_ptr->create_entity(arch);
        Mesh2D *q = &((Mesh2D *)quad.chunk->buffers[0])[quad.idx];
        q->point_count = 4;
        q->points[0] = (Point2D){ -0.9f,  0.9f };
        q->points[1] = (Point2D){ -0.9f,  0.6f };
        q->points[2] = (Point2D){ -0.6f,  0.6f };
        q->points[3] = (Point2D){ -0.6f,  0.9f };
        q->r = 1.0f; q->g = 0.5f; q->b = 0.1f; q->a = 1.0f;
    }

    // Render pass — plugin owns the clear and present
    MTLRenderPassDescriptor *rpd = view.currentRenderPassDescriptor;
    if (!rpd) return;
    rpd.colorAttachments[0].clearColor = MTLClearColorMake(0.08, 0.08, 0.12, 1.0);
    rpd.colorAttachments[0].loadAction = MTLLoadActionClear;

    id<MTLCommandBuffer>         cmdbuf = [queue commandBuffer];
    id<MTLRenderCommandEncoder>  enc    = [cmdbuf renderCommandEncoderWithDescriptor:rpd];
    [enc setRenderPipelineState:g_pipeline];

    // Query ECS for all Mesh2D entities
    ComponentDescriptor *q_descs[] = { g_mesh2d_desc };
    Archetype q_arch = { 1, q_descs };
    ChunkContainer *containers[64];
    size_t n = world_ptr->query(q_arch, containers, 64);

    for (size_t ci = 0; ci < n; ci++) {
        ChunkContainer *container = containers[ci];
        for (size_t chi = 0; chi < container->chunks_count; chi++) {
            Chunk  *chunk  = &container->chunks[chi];
            Mesh2D *meshes = (Mesh2D *)chunk->buffers[0];

            for (size_t ei = 0; ei < chunk->entities_count; ei++) {
                Mesh2D *mesh = &meshes[ei];
                if (mesh->point_count < 3) continue;

                // Expand to triangle list via fan from points[0]
                size_t tri_count = mesh->point_count - 2;
                float verts[(MESH2D_MAX_POINTS - 2) * 6];
                size_t vi = 0;
                for (size_t i = 1; i + 1 < mesh->point_count; i++) {
                    verts[vi++] = mesh->points[0].x;
                    verts[vi++] = mesh->points[0].y;
                    verts[vi++] = mesh->points[i].x;
                    verts[vi++] = mesh->points[i].y;
                    verts[vi++] = mesh->points[i + 1].x;
                    verts[vi++] = mesh->points[i + 1].y;
                }

                float color[4] = { mesh->r, mesh->g, mesh->b, mesh->a };

                [enc setVertexBytes:verts
                             length:vi * sizeof(float)
                            atIndex:0];
                [enc setFragmentBytes:color
                               length:sizeof(color)
                              atIndex:0];
                [enc drawPrimitives:MTLPrimitiveTypeTriangle
                        vertexStart:0
                        vertexCount:(NSUInteger)(tri_count * 3)];
            }
        }
    }

    [enc endEncoding];
    [cmdbuf presentDrawable:view.currentDrawable];
    [cmdbuf commit];
}

static ComponentDescriptor *g_writes_buf[1];

PluginState qubics_plugin(RegistryApi registry) {
    g_mesh2d_desc     = registry.component_register(sizeof(Mesh2D), "Mesh2D");
    g_pipeline        = nil;
    g_entities_created = false;

    g_writes_buf[0] = g_mesh2d_desc;

    SystemDescriptor *descs = malloc(sizeof(SystemDescriptor));
    descs[0] = (SystemDescriptor){
        .run    = mesh2d_system,
        .reads  = { 0, NULL },
        .writes = { 1, g_writes_buf },
    };

    return (PluginState){ .descriptors = descs, .count = 1 };
}
