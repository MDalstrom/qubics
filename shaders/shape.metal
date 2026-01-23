#include <metal_stdlib>
using namespace metal;

struct VertexOut {
    float4 position [[position]];
    float4 color;
};

vertex VertexOut vertex_main(uint vertexID [[vertex_id]],
                             device const float *vertices [[buffer(0)]],
                             device const float *colors [[buffer(1)]]) {
    VertexOut out;
    uint vid = vertexID * 4;  // Now expecting 4 floats per vertex (x,y,z,w)
    float w = vertices[vid+3];
    out.position = float4(vertices[vid] / w, vertices[vid+1] / w, vertices[vid+2] / w, 1.0);
    uint cid = vertexID * 4;
    out.color = float4(colors[cid], colors[cid+1], colors[cid+2], colors[cid+3]);
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]]) {
    return in.color;
}
