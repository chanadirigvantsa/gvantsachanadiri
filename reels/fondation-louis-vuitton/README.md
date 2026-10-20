# Fondation Louis Vuitton: a history

**The video:** [`out/fondation-louis-vuitton-history.mp4`](out/fondation-louis-vuitton-history.mp4) is one narrated 9:16 film (1080×1920, 30 fps, H.264 + AAC, 2 min 54 s). It fits Instagram's 3-minute Reels limit and also works on TikTok. Use [`out/fondation-louis-vuitton-history-cover.jpg`](out/fondation-louis-vuitton-history-cover.jpg) as the cover frame.

It ends on the Fondation's 12th birthday: it opened on 20 October 2014.

| Chapter | What it covers |
| --- | --- |
| 1. The story | 2001 to 2014: the meeting, the plan, the build, the cancelled permit, the rescue in Parliament, the opening |
| 2. In numbers | 12 sails, ~3,600 glass panels, 19,000 Ductal panels, 11 galleries, 350 seats, 55 years |
| 3. The design | The sketch, 19th-century glass, aerospace software, the water, the view |
| 4. The shows | Buren, Shchukin, Schiele & Basquiat, Morozov, Basquiat × Warhol, Rothko, Hockney, Richter |

Everything is drawn from code: kinetic type and original abstract illustrations, with no photos or artwork reproductions. A British male storyteller narrates each scene, and the music ducks under the voice. The voice is [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M), an open-source text-to-speech model under the Apache 2.0 licence, and the music is synthesised, so there are no image, voice or music rights to clear. French names (Arnault, Bois de Boulogne, Fondation Louis Vuitton, Buren, La Défense) are spoken with French pronunciation.

## Caption

> 12 years ago today, a ship of glass landed in the Bois de Boulogne. 🛳️
> The story of the Fondation Louis Vuitton in four chapters: a meeting with Frank Gehry, a cancelled permit and a vote in Parliament; the building in numbers; how Gehry built a cloud of glass; and twelve years of blockbuster shows.
> Which one did you see? 🎨
>
> #FondationLouisVuitton #FrankGehry #ParisArchitecture #ArtHistory #Paris #MuseumLovers #Architecture #ContemporaryArt

## Facts and sources

- 2001: Bernard Arnault meets Frank Gehry. Construction ran from March 2008 to October 2014, and the Fondation opened on 20 October 2014 ([Wikipedia](https://en.wikipedia.org/wiki/Louis_Vuitton_Foundation)).
- 20 January 2011: the Paris administrative court annuls the building permit. Parliament then declares the project of general interest, "a major work of art for the whole world". The Constitutional Council rejects the challenge on 24 February 2012 ([The Fashion Law](https://www.thefashionlaw.com/the-making-of-one-of-the-worlds-most-magnificent-museums/), [Wikipedia](https://en.wikipedia.org/wiki/Louis_Vuitton_Foundation)).
- 12 glass sails, about 3,600 glass panels (some sources give 3,584) and 19,000 Ductal panels ([LVMH](https://www.lvmh.com/commitment-in-action/for-philanthropy/the-fondation-louis-vuitton), [Connexion France](https://www.connexionfrance.com/magazine/plain-sailing-not-for-the-paris-art-museum-inspired-by-a-ship/232677)).
- David Hockney 25 (9 April – 1 September 2025): more than 400 works and over 900,000 visitors ([LVMH](https://www.lvmh.com/en/commitment-in-action/for-philanthropy/the-fondation-louis-vuitton), [La Gazette France](https://www.lagazettefrance.fr/article/2025-annee-faste-pour-les-musees-et-monuments)).
- The figures for the Shchukin (2016–17) and Morozov (2021–22) visitors, the 11 galleries, the 350-seat auditorium and the 55-year land grant are widely reported. Check them against the Fondation's press kit before you post.

This is an unofficial personal project. It uses no Louis Vuitton logos or monogram, and it is not affiliated with the Fondation.

## Re-render or edit

```sh
pip install kokoro-onnx           # for the narrator
python3 make_reels.py             # the full film, narrated (about 10 minutes on 4 cores)
python3 make_reels.py --shorts    # or four separate short reels (40 to 55 s each)
python3 make_reels.py --no-voice  # music only
python3 make_reels.py --preview 5 # one still per scene of the film in preview/
```

The script needs Python 3 with Pillow and numpy, plus ffmpeg. The voice model (about 350 MB) downloads into `tts/` on the first narrated run.

- **On-screen text** lives in the `REELS` list in `make_reels.py`. The film (`FILM`) is assembled from those scenes plus three chapter cards and a closing card.
- **The spoken script** is the `NARRATION` list, one line per scene. Wrap French words in `{braces}` to have them spoken in French, and add names the voice mispronounces to `PRON`.
- **The voice** is set by `VOICE` (now `bm_fable`, British male storyteller). Other options include `bm_george` (British male), `bf_emma` (British female), `af_heart` (US female) and `am_michael` (US male). `VO_SPEED` sets the pace.

Each scene stretches to fit its narration line, and the progress bar and music follow.
