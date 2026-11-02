"""Rebuild the research film picture, subtitles, poster, transcripts and chapters."""
import argparse
from itertools import pairwise
import json
import math
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image
import plates
from transcripts import write_transcripts

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MEDIA = REPO / "docs/video/research"


def write_captions(cues, path):
    def timestamp(ms):
        seconds, milli = divmod(ms, 1000)
        minutes, second = divmod(seconds, 60)
        hours, minute = divmod(minutes, 60)
        return f"{hours:02}:{minute:02}:{second:02}.{milli:03}"

    blocks = [
        f"{timestamp(c['start_ms'])} --> {timestamp(c['end_ms'])}\n" + "\n".join(c['lines'])
        for c in cues
    ]
    path.write_text("WEBVTT\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8")


def validate(edition):
    shots, scenes, cues = edition["shots"], edition["scenes"], edition["captions"]
    fps, duration = edition["fps"], edition["duration"]
    if scenes[0]["start"] != 0 or scenes[-1]["end"] != duration:
        raise ValueError("The chapter range must cover the duration.")
    if any(s["end"] != n["start"] for s, n in pairwise(scenes)):
        raise ValueError("Chapter times must be contiguous.")
    if any(s["start_frame"] >= n["start_frame"] for s, n in pairwise(shots)):
        raise ValueError("Shot start frames must increase.")
    for scene in scenes:
        members = [sh for sh in shots if sh["scene"] == scene["id"]]
        if not members or members[0]["start_frame"] != scene["start"] * fps:
            raise ValueError(f"First shot must begin on its chapter boundary: {scene['id']}")
    if any(c["end_ms"] > n["start_ms"] for c, n in pairwise(cues)):
        raise ValueError("Captions overlap.")
    if any(not 0 <= c["start_ms"] < c["end_ms"] <= duration*1000 for c in cues):
        raise ValueError("A caption is outside the narration duration.")
    text = " ".join(" ".join(c["lines"]) for c in cues)
    if text != " ".join(s["text"] for s in shots):
        raise ValueError("Captions must contain the full spoken transcript.")


def render_frames(edition, work, output):
    shots = edition["shots"]
    fps = edition["fps"]
    chapter_start = {s["start"] * fps for s in edition["scenes"]}
    chapters = {s["id"]: i for i,s in enumerate(edition["scenes"])}
    entries = []
    previous = None
    for i, shot in enumerate(shots):
        start = shot["start_frame"]
        end = shots[i+1]["start_frame"] if i+1 < len(shots) else round(edition["duration"]*fps)
        picture = plates.page(shot["shot"], chapters[shot["scene"]])
        path = work/f"shot-{i:02}.png"
        picture.save(path)
        if i == 0:
            picture.save(output/"poster.jpg", quality=92, subsampling=0, optimize=True)
        hold = end - start
        if previous is not None and start not in chapter_start:
            # Six-frame dissolve between related shots; each chapter begins on its own keyframe.
            for j in range(1,7):
                mix = (1 - math.cos(j*math.pi/7))/2
                blended = Image.blend(previous, picture, mix)
                blend_path = work/f"mix-{i:02}-{j}.png"
                blended.save(blend_path, compress_level=2)
                entries.append((blend_path, 1))
            hold -= 6
        if hold <= 0:
            raise ValueError(f"Shot too short for the chapter transition: {shot['shot']}")
        entries.append((path, hold))
        previous = picture

    playlist = ["ffconcat version 1.0"]
    for path, frames in entries:
        # All filenames are generated here, relative to the temporary concat manifest.
        playlist += [f"file {path.name}", f"option framerate {fps}", f"duration {frames/fps:.9f}"]
    playlist += [f"file {entries[-1][0].name}", f"option framerate {fps}"]
    manifest = work/"picture.ffconcat"
    manifest.write_text("\n".join(playlist)+"\n")
    return manifest


def write_chapters(edition, work, output):
    fps, duration = edition["fps"], edition["duration"]
    scenes = [{k:s[k] for k in ("id","title","start","end")} for s in edition["scenes"]]
    timeline = {"fps":fps, "frames":round(fps*duration), "duration":duration, "scenes":scenes}
    (output/"timeline.json").write_text(json.dumps(timeline, indent=2)+"\n")
    chapters = work/"chapters.ffmeta"
    blocks = []
    for s in scenes:
        title = s["title"]
        if any(k in title for k in "\\;=#\n"):
            raise ValueError("Chapter title contains an FFmetadata control character.")
        blocks.append(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={s['start']*1000}\nEND={s['end']*1000}\ntitle={title}\n")
    chapters.write_text(";FFMETADATA1\n"+"".join(blocks))
    return chapters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New or empty output directory.")
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"), help="Path to FFmpeg with libx264 and mov_text.")
    parser.add_argument("--font-dir", type=Path, default=Path("/System/Library/Fonts/Supplemental"))
    parser.add_argument("--mono-font", type=Path, default=Path("/System/Library/Fonts/Menlo.ttc"))
    parser.add_argument("--figure", type=Path, default=REPO/"docs/figures/figure-1.png")
    parser.add_argument("--audio-from", type=Path, default=MEDIA/"match-words-with-deeds.mp4",
                        help="A finished MP4/M4A containing the matched AAC narration.")
    args = parser.parse_args()
    output = args.out.resolve()
    if not args.ffmpeg:
        parser.error("Install FFmpeg or pass --ffmpeg with its path.")
    if output.exists() and any(output.iterdir()):
        parser.error("--out must be empty to preserve any existing media.")
    if not args.audio_from.is_file():
        parser.error("--audio-from must be a finished MP4 or M4A with the recorded narration.")
    edition = json.loads((HERE/"edition.json").read_text())
    validate(edition)
    for name in ("Arial.ttf","Arial Bold.ttf","Georgia.ttf","Georgia Italic.ttf"):
        if not (args.font_dir/name).is_file():
            parser.error(f"Missing {name}; supply --font-dir with these four fonts.")
    if not args.mono_font.is_file():
        parser.error("Missing monospaced typeface; supply --mono-font.")
    plates.configure(args.figure, args.font_dir, args.mono_font)
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as temporary:
        work = Path(temporary)
        manifest = render_frames(edition, work, output)
        chapters = write_chapters(edition, work, output)
        write_captions(edition["captions"], output/"captions.en.vtt")
        write_transcripts(edition, output)
        keyframes = ",".join(str(s["start"]) for s in edition["scenes"])
        subprocess.run([
            args.ffmpeg,"-hide_banner","-nostdin","-loglevel","error","-n",
            "-f","concat","-safe","0","-i",str(manifest),"-i",str(args.audio_from),
            "-i",str(output/"captions.en.vtt"),"-f","ffmetadata","-i",str(chapters),
            "-map","0:v","-map","1:a:0","-map","2:s","-map_chapters","3",
            "-metadata","title="+edition["title"],"-metadata:s:a:0","language=eng",
            "-metadata:s:s:0","language=eng","-disposition:s:0","0",
            "-vf",f"fps={edition['fps']},setsar=1,format=yuv420p",
            "-force_key_frames",keyframes,"-c:v","libx264","-preset","veryfast","-crf","17",
            "-threads","4","-g","120","-profile:v","high","-level","4.1",
            "-c:a","copy","-c:s","mov_text","-t",str(edition["duration"]),"-movflags","+faststart",
            str(output/"match-words-with-deeds.mp4")
        ], check=True)


if __name__ == "__main__":
    main()
