#include <metal_stdlib>
using namespace metal;

struct Vertex {
    float2 position [[attribute(0)]];
};

struct VertexOut {
    float4 position [[position]];
};

vertex VertexOut vertex_main(uint vertexID [[vertex_id]],
                             constant Vertex *vertices [[buffer(0)]]) {
    VertexOut out;
    out.position = float4(vertices[vertexID].position, 0.0, 1.0);
    return out;
}

fragment float4 fragment_main(constant float4 &color [[buffer(0)]]) {
    return color;
}
