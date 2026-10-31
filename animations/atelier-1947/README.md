# Atelier, Paris 1947

A 10-second vertical (9:16, 1080×1920, 24 fps) animation in the manner of a
1940s French fashion illustration: gouache and ink on cream paper, in
charcoal, midnight blue and soft gold.

At night on a quiet Paris avenue, a Haussmann building is dark except for one
lit window on the étage noble. The camera glides in one continuous move with
no cuts, passes through the open casement and comes to rest in a couture
atelier. There, a man in a white smock pins ivory fabric on a dress form:
a fitted jacket with a cinched waist over a full pleated skirt. Sketches are
pinned to the walls, a vase of lily of the valley stands on the table, and a
brass lamp gives warm light.

Every frame is painted procedurally in Python. No footage or image models are
used.

| file | contents |
| --- | --- |
| `paint.py` | small gouache/ink toolkit: world-space canvas, textured fills, pressure-varied ink strokes, value noise |
| `exterior.py` | the facade, wrought-iron balconies, lit window, chestnut trees |
| `interior.py` | the atelier, the dress form and garment, the couturier |
| `render.py` | camera move (dolly with parallax), compositing, paper grain, encoding |
| `atelier-1947.mp4` | the rendered film |

To render it again (requires numpy, Pillow and ffmpeg):

```sh
python3 render.py out          # writes out/frames/*.png and out/atelier-1947.mp4
```
