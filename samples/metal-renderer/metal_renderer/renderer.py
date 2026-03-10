import ctypes
from Metal import MTLLoadActionClear, MTLPrimitiveTypeTriangle  # ty:ignore[unresolved-import]
from objc import ObjCInstance  # ty:ignore[unresolved-import]
from qubics.types import SystemFn


VERTEX_SHADER = """
#include <metal_stdlib>
using namespace metal;

struct VertexOut {
    float4 position [[position]];
    float4 color;
};

vertex VertexOut vertex_main(uint vertexID [[vertex_id]]) {
    VertexOut out;
    
    float2 positions[3] = {
        float2(0.0, 0.5),
        float2(-0.5, -0.5),
        float2(0.5, -0.5)
    };
    
    float4 colors[3] = {
        float4(1.0, 0.0, 0.0, 1.0),
        float4(0.0, 1.0, 0.0, 1.0),
        float4(0.0, 0.0, 1.0, 1.0)
    };
    
    out.position = float4(positions[vertexID], 0.0, 1.0);
    out.color = colors[vertexID];
    
    return out;
}

fragment float4 fragment_main(VertexOut in [[stage_in]]) {
    return in.color;
}
"""


def mk_system(world_ptr):
    pipeline_state = None
    
    def system(world_ptr, context_ptr):
        nonlocal pipeline_state
        
        render_context = ctypes.cast(context_ptr, ctypes.POINTER(ctypes.c_void_p * 3)).contents
        
        view = ObjCInstance(render_context[0])
        device = ObjCInstance(render_context[1])
        command_queue = ObjCInstance(render_context[2])
        
        if pipeline_state is None:
            library = device.newLibraryWithSource_options_error_(VERTEX_SHADER, None, None)[0]
            
            vertex_function = library.newFunctionWithName_("vertex_main")
            fragment_function = library.newFunctionWithName_("fragment_main")
            
            pipeline_descriptor = ObjCInstance(device).newRenderPipelineDescriptor()
            pipeline_descriptor.setVertexFunction_(vertex_function)
            pipeline_descriptor.setFragmentFunction_(fragment_function)
            pipeline_descriptor.colorAttachments().objectAtIndexedSubscript_(0).setPixelFormat_(80)
            
            pipeline_state = device.newRenderPipelineStateWithDescriptor_error_(pipeline_descriptor, None)[0]
        
        command_buffer = command_queue.commandBuffer()
        render_pass_descriptor = view.currentRenderPassDescriptor()
        
        if render_pass_descriptor:
            render_pass_descriptor.colorAttachments().objectAtIndexedSubscript_(0).setLoadAction_(MTLLoadActionClear)
            render_pass_descriptor.colorAttachments().objectAtIndexedSubscript_(0).setClearColor_((0.1, 0.1, 0.1, 1.0))
            
            encoder = command_buffer.renderCommandEncoderWithDescriptor_(render_pass_descriptor)
            encoder.setRenderPipelineState_(pipeline_state)
            encoder.drawPrimitives_vertexStart_vertexCount_(MTLPrimitiveTypeTriangle, 0, 3)
            encoder.endEncoding()
            
            command_buffer.presentDrawable_(view.currentDrawable())
        
        command_buffer.commit()
    
    return SystemFn(system)

