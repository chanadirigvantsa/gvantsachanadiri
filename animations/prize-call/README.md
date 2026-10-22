# მოგებული ტელევიზორი · The Prize Call

A one-minute comedic 3D cartoon (fictional). Tsiuri is at home in her cozy Tbilisi
apartment when an unknown number calls. The caller is phoning from a prison cell. She has "won" a giant television and only
needs to send a little money first. She's thrilled, pays straight away and waits
proudly for her prize. One week later, she's still waiting.

- `prize-call.mp4`: the rendered film (1920×1080, 16:9, 30 fps, about 57 s)
- `index.html`: the same animation playing live in the browser (Three.js), with a seek bar

The dialogue is spoken in English, with Georgian subtitles. The voices are
synthesized with espeak-ng's English voices, and the mouths are lip-synced to each
voice line's loudness, frame by frame. Tsiuri pays with a card drawn in the style of the classic
Georgian "Mono" phone card (no operator logo). The banking app is a generic design.

## Rebuild

```sh
# voices, music, sound effects -> soundtrack.m4a + timeline.js
node animations/prize-call/tools/build-audio.mjs
# frames -> prize-call.mp4 (needs Playwright + ffmpeg)
node animations/prize-call/tools/render.mjs
# or just a few test frames
node animations/prize-call/tools/render.mjs --stills 3,14.6,36 /tmp/stills
```

Vendored: three.js r160 (MIT) and Noto Sans Georgian (OFL), see `vendor/`.
