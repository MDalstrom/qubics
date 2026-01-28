#include <metal_stdlib>
using namespace metal;

vertex float4 vertex_main(
	const device float4* vertices [[buffer(0)]],
	const device float4x4* instanceMatrices [[buffer(1)]],
	const device float4x4& viewProjectionMatrix [[buffer(2)]],
	uint vertexId   [[vertex_id]],
	uint instanceId [[instance_id]]
) {
	float4 world = instanceMatrices[instanceId] * vertices[vertexId];
	world = viewProjectionMatrix * world;
	return world;
};

fragment float4 fragment_main(float4 in [[stage_in]]) {
	return float4(0.6, 1.0, 0.4, 1.0);
}
