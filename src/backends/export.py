import pygame
import numpy as np


def run(
    player,
    *,
    config
):
    import imageio
    surface = pygame.Surface((config['width'], config['height']))
    total_frames = config['duration'] * config['fps']
    output_file = config['output']
    print(f"Exporting {total_frames} frames to {output_file}...")
    
    with imageio.get_writer(output_file, fps=config['fps']) as writer:
        for frame_num in range(total_frames):
            surface.fill(config['bg_color'])
            player(surface)
            frame_data = pygame.surfarray.array3d(surface)
            frame_data = np.transpose(frame_data, (1, 0, 2))
            writer.append_data(frame_data) #pyright: ignore
            if (frame_num + 1) % config['fps'] == 0:
                print(f"  Progress: {frame_num + 1}/{total_frames} frames ({(frame_num + 1) // config['fps']}s)")
    
    print(f"Video exported successfully to {output_file}")

