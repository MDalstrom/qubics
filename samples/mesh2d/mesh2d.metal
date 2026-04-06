#include <metal_stdlib>
using namespace metal;

struct VertexOut {
    float4 position [[position]];
};

vertex VertexOut vert_main(
    uint               vid    [[vertex_id]],
    uint               iid    [[instance_id]],
    constant float2   *verts  [[buffer(0)]],
    constant float4x4 *models [[buffer(1)]],
    constant float4x4 &vp     [[buffer(2)]]
) {
    VertexOut out;
    out.position = vp * models[iid] * float4(verts[vid], 0.0, 1.0);
    return out;
}

fragment float4 frag_main(
    VertexOut        in    [[stage_in]],
    constant float4 &color [[buffer(0)]]
) {
    return color;
}
