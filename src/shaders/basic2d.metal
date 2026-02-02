#include <metal_stdlib>
using namespace metal;

struct VertexOut {
    float4 position [[position]];
    float4 color;
};

vertex VertexOut vertex_2d(
    const device float2* vertices [[buffer(0)]],
    const device float4* colors [[buffer(1)]],
    const device float3x3* instanceMatrices [[buffer(2)]],
    const device float3x3& viewProjectionMatrix [[buffer(3)]],
    uint vertexId   [[vertex_id]],
    uint instanceId [[instance_id]]
) {
    VertexOut out;
    float3 source = float3(vertices[vertexId].x, vertices[vertexId].y, 1);
    float3 world = instanceMatrices[instanceId] * source;
    world = viewProjectionMatrix * world;
    out.position = float4(world.x, world.y, 0, 0);
    out.color = colors[vertexId];
    return out;
};

fragment float4 fragment_2d(VertexOut in [[stage_in]]) {
    return in.color;
}

