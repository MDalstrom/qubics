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
            "-c:v", "h264_videotoolbox",
            "-b:v", "10M",
            "-pix_fmt", "yuv420p",
            self.output_path,
        ]

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

    def write_frame(self, data: bytes):
        if not self.process or not self.process.stdin:
            return False
            
        expected_size = self.width * self.height * 4
        if len(data) != expected_size:
            print(f"Warning: Frame size mismatch! Expected {expected_size}, got {len(data)}")
            return False

        try:
            self.process.stdin.write(data)
            self.process.stdin.flush()
            return True
        except (BrokenPipeError, ValueError) as e:
            print(f"Broken pipe! Error: {e}")
            if self.process.stderr:
                stderr = self.process.stderr.read()
                print("FFmpeg stderr:")
                print(stderr.decode())
            return False

    def finish(self):
        if not self.process:
            return
            
        if self.process.stdin:
            try:
                # Flush any remaining data
                self.process.stdin.flush()
                # Close stdin to signal end of input
                self.process.stdin.close()
            except Exception as e:
                print(f"[WARNING] Error closing stdin: {e}")
        
        # Wait for FFmpeg to finish encoding
        try:
            returncode = self.process.wait(timeout=10)
            if returncode != 0:
                print(f"[WARNING] FFmpeg exited with code {returncode}")
                if self.process.stderr:
                    stderr = self.process.stderr.read()
                    print("FFmpeg stderr:", stderr.decode())
        except Exception as e:
            print(f"[ERROR] Error waiting for FFmpeg: {e}")
            self.process.kill()
        
        self.process = None

