# NeuroLab research demo video

workflow: product-launch-video
flow: autonomous
status: waiting for real browser footage or working browser control

## Intent

Show the actual application as a research walkthrough. Use real screen footage of setup, deterministic processing or clearly labeled saved replay, results, uncertainty, a focused follow-up and evidence export. Do not reconstruct screens or fabricate successful activity to substitute for footage.

## Output

Landscape 1920 by 1080 MP4, target about 2 minutes 50 seconds and no more than the program's confirmed limit. Include natural-sounding generated English narration, burned-in subtitles and a separate SRT. Use the existing recording guide as the spoken/screen sequence; wording can be edited to match the actual captured actions while preserving scientific qualifications.

## Voice preference

Owner explicitly selected a natural-sounding generated narrator. The first local preview uses Kokoro `bm_george` at speed 0.96 through HyperFrames 0.8.209. It is synthetic speech, not a human recording or a cloned personal voice. Preview files are in ignored `output/demo-video/`; they do not contain browser footage. Actual screen capture remains unavailable because browser control reports `CUA_REPL_ENABLED_SURFACES is required`. Approval has been received, but no browser surface is attached. No cloud speech account or paid voice API was used for the preview.

The full local narration is now available at `output/demo-video/full-narration/neurolab-narration.mp3`, with a matching SRT and metadata. Its verified duration is 166.848 seconds. See `RECORDING_CUES.md` for the timed capture plan. Audio listening review and final footage alignment remain pending.

## Scientific boundaries

Meta remains paused after exhausted credits. A saved timeline must say replay of a previously completed deterministic run. Numeric results must match the selected run and source hash. The maize illustration is illustrative, not observed geometry or a calibrated crop simulator. Candidate genotypes remain exploratory leads; confounding, uncertainty and stopping criteria remain audible/visible.

## Editing requirements

Keep source, status and important numeric/caveat labels readable. Shortened waits must be labeled. Align narration and captions to the final actual cuts; the preview captions are sentence-level timing from the synthesized utterances, not final walkthrough timestamps. Preserve the original footage and exports. Hide credentials, personal account information and unrelated desktop content. No music is needed.

## Next required input

Working browser control and a safe recording path, or an owner-provided screen recording. A final narrated application walkthrough cannot be delivered from the voice preview alone. Do not publish or submit a video automatically.
