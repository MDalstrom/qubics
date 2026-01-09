"""
Video export backend - renders frames to video file.
Pure rendering backend, no simulation logic.
"""
import pygame
import numpy as np
import imageio


class VideoBackend:
    """Video export backend for offline rendering to file."""
    
    def __init__(self, width: int, height: int, bg_color: tuple[int, int, int], 
                 fps: int, output_file: str, total_frames: int):
        self.surface = pygame.Surface((width, height))
        self.bg_color = bg_color
        self.writer = imageio.get_writer(output_file, fps=fps)
        self.output_file = output_file
        self.fps = fps
        self.total_frames = total_frames
        self.frame_count = 0
        print(f"Exporting {total_frames} frames to {output_file}...")
    
    def begin_frame(self) -> None:
        """Clear surface."""
        self.surface.fill(self.bg_color)
    
    def get_surface(self):
        """Get drawing surface."""
        return self.surface
    
    def end_frame(self) -> None:
        """Export frame to video file."""
        frame_data = pygame.surfarray.array3d(self.surface)
        frame_data = np.transpose(frame_data, (1, 0, 2))
        self.writer.append_data(frame_data)
        self.frame_count += 1
    
    def should_quit(self) -> bool:
        """Check if all frames are rendered."""
        return self.frame_count >= self.total_frames
    
    def report_progress(self, frame_num: int, total: int) -> None:
        """Print progress."""
        if (frame_num + 1) % self.fps == 0:
            print(f"  Progress: {frame_num + 1}/{total} frames ({(frame_num + 1) // self.fps}s)")
    
    def cleanup(self) -> None:
        """Close video writer."""
        self.writer.close()
        print(f"Video exported successfully to {self.output_file}")

