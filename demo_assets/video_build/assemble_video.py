"""
Assemble the final demo video.

Plan:
  Section 1 (Hook)           — frame 01 + s1_hook.mp3
  Section 2 (Architecture)   — frame 02 + s2_architecture.mp3
  Section 3a (detect)        — frame 03 + s3a_detect.mp3
  Section 3b (triage)        — frame 03 + s3b_triage.mp3
  Section 3c (cost)          — frame 03 + s3c_cost.mp3
  Section 3d (approval)      — frame 03 + s3d_approval.mp3
  Section 3e (remediation)   — frame 03 + s3e_remediation.mp3
  Section 3f (post-mortem)   — frame 03 + s3f_postmortem.mp3
  Section 4 (all scenarios)  — frame 04 + s4_allscenarios.mp3
  Section 5 (tests)          — frame 05 + s5_tests.mp3
  Section 6 (maestro)        — frame 06 + s6_maestro.mp3
  Section 7 (close)          — frame 07 + s7_close.mp3
"""
import subprocess, os
from pathlib import Path

FRAMES = Path("/home/user/neurascale-ops/demo_assets/video_build/frames")
AUDIO  = Path("/home/user/neurascale-ops/demo_assets/video_build/audio")
SEGS   = Path("/home/user/neurascale-ops/demo_assets/video_build/sections")
OUT    = Path("/home/user/neurascale-ops/demo_assets")
SEGS.mkdir(exist_ok=True)

def audio_duration(path):
    r = subprocess.run(
        ["ffprobe","-v","quiet","-show_entries","format=duration",
         "-of","default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True)
    return float(r.stdout.strip())

def make_segment(seg_id, frame_png, audio_mp3, out_mp4, extra_pad=0.4):
    dur = audio_duration(audio_mp3) + extra_pad
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(frame_png),
        "-i", str(audio_mp3),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-t", str(dur),
        "-shortest",
        str(out_mp4)
    ]
    print(f"  Building segment {seg_id} ({dur:.1f}s)...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr[-300:]}")
    else:
        print(f"  ✓ {out_mp4.name}")

# ── Build each segment ────────────────────────────────────────────────────
segments = [
    ("s01", "01_title_hook.png",       "s1_hook.mp3",         "seg01_hook.mp4"),
    ("s02", "02_architecture.png",     "s2_architecture.mp3", "seg02_arch.mp4"),
    ("s03", "03_oomkill_pipeline.png", "s3a_detect.mp3",      "seg03a_detect.mp4"),
    ("s04", "03_oomkill_pipeline.png", "s3b_triage.mp3",      "seg03b_triage.mp4"),
    ("s05", "03_oomkill_pipeline.png", "s3c_cost.mp3",        "seg03c_cost.mp4"),
    ("s06", "03_oomkill_pipeline.png", "s3d_approval.mp3",    "seg03d_approval.mp4"),
    ("s07", "03_oomkill_pipeline.png", "s3e_remediation.mp3", "seg03e_remediation.mp4"),
    ("s08", "03_oomkill_pipeline.png", "s3f_postmortem.mp3",  "seg03f_postmortem.mp4"),
    ("s09", "04_all_scenarios.png",    "s4_allscenarios.mp3", "seg04_allscenarios.mp4"),
    ("s10", "05_pytest_17_passing.png","s5_tests.mp3",        "seg05_tests.mp4"),
    ("s11", "06_maestro_case.png",     "s6_maestro.mp3",      "seg06_maestro.mp4"),
    ("s12", "07_closing_impact.png",   "s7_close.mp3",        "seg07_close.mp4"),
]

print("Building segments...")
for sid, frame, audio, out in segments:
    make_segment(sid, FRAMES / frame, AUDIO / audio, SEGS / out)

# ── Concatenate all segments ──────────────────────────────────────────────
concat_list = SEGS / "concat.txt"
with open(concat_list, "w") as f:
    for _, _, _, out in segments:
        f.write(f"file '{(SEGS / out).absolute()}'\n")

final = OUT / "neurascale_ops_demo.mp4"
print(f"\nConcatenating {len(segments)} segments → {final.name} ...")
cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", str(concat_list),
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart",
    str(final)
]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print(f"ERROR: {r.stderr[-500:]}")
else:
    size_mb = os.path.getsize(final) / 1024 / 1024
    print(f"\n✓ Final video: {final}")
    print(f"  Size: {size_mb:.1f} MB")
    # duration
    dur_r = subprocess.run(
        ["ffprobe","-v","quiet","-show_entries","format=duration",
         "-of","default=noprint_wrappers=1:nokey=1", str(final)],
        capture_output=True, text=True)
    total_sec = float(dur_r.stdout.strip())
    print(f"  Duration: {int(total_sec//60)}m {int(total_sec%60)}s")
    print(f"\n  Upload to Devpost / YouTube as demo video.")
