# Fondation Louis Vuitton: a history in four reels

A personal series of four 9:16 reels (1080×1920, 30 fps, H.264 + AAC, around 30 s each). They're ready to post on Instagram Reels and TikTok.
Reel 1 lands on the Fondation's 12th birthday: it opened on 20 October 2014.

Everything is drawn from code: kinetic type and original abstract illustrations, with no photos or artwork reproductions. The soundtrack is synthesised, so there are no image or music rights to clear. You can still swap in a trending sound in the app; the cuts land on a steady 60 BPM pulse.

| # | File | Length | Story |
| --- | --- | --- | --- |
| 1 | [`out/01-thirteen-years.mp4`](out/01-thirteen-years.mp4) | 31.6 s | 2001 to 2014: the meeting, the plan, the build, the cancelled permit, the rescue in Parliament, the opening |
| 2 | [`out/02-by-the-numbers.mp4`](out/02-by-the-numbers.mp4) | 31.6 s | 12 sails, ~3,600 glass panels, 19,000 Ductal panels, 11 galleries, 350 seats, 55 years |
| 3 | [`out/03-how-gehry-did-it.mp4`](out/03-how-gehry-did-it.mp4) | 27.6 s | Five design secrets: the sketch, 19th-century glass, aerospace software, the water, the view |
| 4 | [`out/04-blockbusters.mp4`](out/04-blockbusters.mp4) | 31.8 s | Buren, Shchukin, Schiele & Basquiat, Morozov, Basquiat × Warhol, Rothko, Hockney, Richter |

Each reel has a matching `-cover.jpg` in `out/` to use as the cover frame.

## Captions

**Reel 1: 13 years, 3,600 panes of glass, 1 act of Parliament**
> 12 years ago today, a ship of glass landed in the Bois de Boulogne. 🛳️
> It took a meeting with Frank Gehry in 2001, a cancelled building permit and a vote in Parliament to get here.
> Part 1/4 of a short history of the Fondation Louis Vuitton.
>
> #FondationLouisVuitton #FrankGehry #ParisArchitecture #ArtHistory #Paris #MuseumLovers #Architecture

**Reel 2: By the numbers**
> 12 sails. ~3,600 curved glass panels. 19,000 concrete panels. One building.
> Which number surprised you? 👇
> Part 2/4.
>
> #FondationLouisVuitton #Gehry #ArchitectureLovers #ParisMuseums #DesignFacts #Paris

**Reel 3: How Gehry built a cloud of glass**
> From a scribble on paper to aerospace software: five design secrets of the Fondation Louis Vuitton.
> Save it for your next trip to Paris. 📌
> Part 3/4.
>
> #FrankGehry #FondationLouisVuitton #ArchitectureDesign #ParisTravel #DesignHistory

**Reel 4: 12 years of blockbuster shows**
> Shchukin, Morozov, Basquiat × Warhol, Rothko, Hockney, Richter: twelve years of some of the biggest art shows Paris has seen.
> Which one did you see? 🎨
> Part 4/4.
>
> #FondationLouisVuitton #ArtExhibition #Rothko #Hockney #Basquiat #ParisArt #ContemporaryArt

## Facts and sources

- 2001: Bernard Arnault meets Frank Gehry. Construction ran from March 2008 to October 2014, and the Fondation opened on 20 October 2014 ([Wikipedia](https://en.wikipedia.org/wiki/Louis_Vuitton_Foundation)).
- 20 January 2011: the Paris administrative court annuls the building permit. Parliament then declares the project of general interest, "a major work of art for the whole world". The Constitutional Council rejects the challenge on 24 February 2012 ([The Fashion Law](https://www.thefashionlaw.com/the-making-of-one-of-the-worlds-most-magnificent-museums/), [Wikipedia](https://en.wikipedia.org/wiki/Louis_Vuitton_Foundation)).
- 12 glass sails, about 3,600 glass panels (some sources give 3,584) and 19,000 Ductal panels ([LVMH](https://www.lvmh.com/commitment-in-action/for-philanthropy/the-fondation-louis-vuitton), [Connexion France](https://www.connexionfrance.com/magazine/plain-sailing-not-for-the-paris-art-museum-inspired-by-a-ship/232677)).
- David Hockney 25 (9 April – 1 September 2025): more than 400 works and over 900,000 visitors ([LVMH](https://www.lvmh.com/en/commitment-in-action/for-philanthropy/the-fondation-louis-vuitton), [La Gazette France](https://www.lagazettefrance.fr/article/2025-annee-faste-pour-les-musees-et-monuments)).
- The figures for the Shchukin (2016–17) and Morozov (2021–22) visitors, the 11 galleries, the 350-seat auditorium and the 55-year land grant are widely reported. Check them against the Fondation's press kit before you post.

This is an unofficial personal project. It uses no Louis Vuitton logos or monogram, and it is not affiliated with the Fondation.

## Re-render or edit

```sh
python3 make_reels.py            # all four (about 3 minutes on 4 cores)
python3 make_reels.py 2 4        # only reels 2 and 4
python3 make_reels.py --preview  # one still per scene in preview/
```

The script needs Python 3 with Pillow and numpy, plus ffmpeg. All the text lives in the `REELS` list in `make_reels.py`. Change a line, re-render, and the timing, progress bars and soundtrack follow.
