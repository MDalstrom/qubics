from __future__ import annotations
import Metal
from typing import Any
from dataclasses import dataclass


@dataclass
class RenderingState:
    device: Metal.MTLDevice
    queue: Metal.MTLCommandQueue
    buffer: Metal.MTLCommandBuffer
    encoder: Metal.MTLRenderCommandEncoder
    descriptor: Any
