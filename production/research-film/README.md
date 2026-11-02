# Rebuilding Match Words with Deeds

This directory contains the source for the 4:30 research film, updated on 2 November 2026 against the final proposal and appendix. The Table A13 scene distinguishes the reported extension from the existing 25-model reproduction. The [delivered media](../../docs/video/research/) includes its English narration, poster, captions, chapter timeline and two transcripts. The October software walkthrough has its own files.

## Rebuild the film

Use Python 3.10 or newer, Pillow, and FFmpeg with the `libx264` and `mov_text` encoders. The original render used Pillow 13.0.0 and FFmpeg 7.1. The picture uses Arial, Arial Bold, Georgia, Georgia Italic, and Menlo from macOS. For another platform, pass a directory containing the four named TrueType files and a path to a monospaced font with `--font-dir` and `--mono-font`. Review line breaks if a typeface changes. Font files are not redistributed.

From the repository root, choose a new or empty output directory.

```sh
python production/research-film/rebuild.py --out /tmp/match-words-with-deeds-preview
```

Pass `--ffmpeg /path/to/ffmpeg` to select an encoder outside your executable search path. The script uses the shipped MP4 as the source of the finished AAC narration and copies that audio stream without re-encoding. It renders the picture from [Figure 1](../../docs/figures/figure-1.png) and the original diagrams, writes the synchronized WebVTT, embeds English subtitles and chapter times, and generates the poster and both transcripts. Intermediate images use a temporary directory.

## Edit a picture or caption

- [edition.json](edition.json) specifies the six chapters, 28 shots, written and synthesis-only pronunciations, frame starts, measured caption intervals and visual notes. Frame numbering begins at zero and caption times are milliseconds from the start of the film. Each cue contains one or two display lines.
- [plates.py](plates.py) draws the evidence graphics and crops the supplied Figure 1. A shot uses its name in the edition file to select a drawing. The six chapter starts are keyframes. Between shots in the same chapter, the picture dissolves over six frames.
- [transcripts.py](transcripts.py) writes the accessible HTML transcript and its Markdown counterpart. Each chapter pairs the narrated text with visual information and links to evidence. The source-table links point to the reviewed repository revision.

For a visual change, edit its drawing or note, run the command into a new directory, and inspect the affected chapter both with and without captions. Check both transcripts if a displayed claim or link changes. The rebuild rejects caption text that diverges from the narration and a chapter that does not start on its first shot.

## Change the narration

A change to spoken words requires a fresh audio recording, its measured cue timings and revised shot and chapter boundaries. The committed `spoken_text` fields record the pronunciation expansions used by Kokoro 0.9.4 with its `af_heart` voice. The model revision is in the edition file. Measure the new cues against the finished audio and update the corresponding transcript text, captions, shots, and timeline. Supply a level-matched MP4 or M4A containing that AAC track with `--audio-from`. Update the displayed running time in both transcripts if the duration changes, then check the beginning, each chapter seek and the last spoken word.
