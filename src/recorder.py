import subprocess
import shutil

if shutil.which("ffmpeg") is None:
    raise RuntimeError("ffmpeg not found")

class FFmpegRecorder:
    def __init__(self, width, height, fps, output_path):
        self.width = width
        self.height = height
        self.fps = fps
        self.output_path = output_path
        self.process = None

    def start(self):
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-pixel_format", "bgra",
            "-video_size", f"{self.width}x{self.height}",
            "-framerate", str(self.fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            self.output_path,
        ]

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            bufsize=0,  # unbuffered
        )

    def write_frame(self, data: bytes):
        assert self.process
        assert self.process.stdin
        
        expected_size = self.width * self.height * 4
        if len(data) != expected_size:
            print(f"Warning: Frame size mismatch! Expected {expected_size}, got {len(data)}")
            return False

        try:
            self.process.stdin.write(data)
            self.process.stdin.flush()  # Important!
            return True
        except BrokenPipeError:
            print("Broken pipe! FFmpeg stderr:")
            assert self.process.stderr
            stderr = self.process.stderr.read()
            print(stderr.decode())
            return False

    def finish(self):
        assert self.process
        assert self.process.stdin

        self.process.stdin.close()
        self.process.wait()
        self.process = None

