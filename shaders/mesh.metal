#include <metal_stdlib>
using namespace metal;

struct VertexIn {
    float2 position [[attribute(0)]];
    float3 color [[attribute(1)]];
};

struct VertexOut {
    float4 position [[position]];
    float3 color;
};

vertex VertexOut vert_main(VertexIn in [[stage_in]]) {
    VertexOut out;
    out.position = float4(in.position, 0.0, 1.0);
    out.color = in.color;
    return out;
}

fragment float4 frag_main(VertexOut in [[stage_in]]) {
    return float4(in.color, 1.0);
}

kernel void integrate(
    device float2* positions,
    device float2* prevPositions,
    device float2* accelerations,
    device float* invMasses,
    constant float& dt,
    uint id [[thread_position_in_grid]]
) {
    float2 temp = positions[id];
    positions[id] += (positions[id] - prevPositions[id]) + accelerations[id] * (dt * dt);
    prevPositions[id] = temp;
    accelerations[id] = float2(0.0);
}

kernel void project(
    device float2* positions [[buffer(0)]],
    device uint2*  edges     [[buffer(1)]],
    device float*  restLen   [[buffer(2)]],
    device float*  invMass   [[buffer(3)]],
    uint id [[thread_position_in_grid]]
) {
    uint2 e = edges[id];
    uint i = e.x;
    uint j = e.y;

    float2 delta = positions[j] - positions[i];
    float len = length(delta);
    if (len < 1e-6) return;

    float diff = (len - restLen[id]) / len;
    float w1 = invMass[i];
    float w2 = invMass[j];
    float wsum = w1 + w2;
    if (wsum == 0.0) return;

    float2 corr = delta * diff / wsum;

    positions[i] += corr * w1;
    positions[j] -= corr * w2;
}