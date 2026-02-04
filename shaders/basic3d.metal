#include <metal_stdlib>
using namespace metal;

struct VertexOut {
	float4 position [[position]];
	float4 color;
};

vertex VertexOut vertex_main(
	const device float4* vertices [[buffer(0)]],
	const device float4* colors [[buffer(1)]],
	const device float4x4* instanceMatrices [[buffer(2)]],
	const device float4x4& viewProjectionMatrix [[buffer(3)]],
	uint vertexId   [[vertex_id]],
	uint instanceId [[instance_id]]
) {
	VertexOut out;
	out.position = instanceMatrices[instanceId] * vertices[vertexId];
	out.position = viewProjectionMatrix * out.position;
	out.color = colors[vertexId];
	return out;
};

fragment float4 fragment_main(VertexOut in [[stage_in]]) {
	return in.color;
}
