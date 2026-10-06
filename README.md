# Gvantsa Chanadiri: Portfolio

A one-page portfolio site for a content manager and creative producer. It's plain HTML with no build step, so GitHub Pages can host it as is.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The site: layout, styles and the built-in editor |
| `content.js` | Your text, projects, links and image list. It overrides the defaults in `index.html` |
| `cv.pdf` | Your CV. The "Download CV (PDF)" link on the About and Contact pages opens this file |
| `images/` | Your photos and videos |

## Put it online (GitHub Pages)

1. On GitHub, open the repo and go to **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**. Pick your branch (`main` once this is merged) and the `/ (root)` folder, then click **Save**.
3. Within a minute or two the site is live at `https://chanadirigvantsa.github.io/gvantsachanadiri/`.

## Edit the content

1. Open the site with `?edit` at the end of the address, for example
   `https://chanadirigvantsa.github.io/gvantsachanadiri/?edit`.
   You can also open `index.html?edit` locally.
2. Click **Edit site**. Click any text with a dashed outline to change it. You can add or remove projects, articles, Instagram tiles and personal projects, and choose photos or videos for each slot.
3. Your changes are saved as a draft in this browser only. Visitors don't see them yet.
4. Click **Download content.js**.
5. Upload the downloaded `content.js` to the repo, replacing the old file. If you chose photos, videos or a CV, upload those exact files (same file names) into the `images/` folder.
6. Commit. The live site updates within a minute or two.

## Projects and social projects

- **Work projects:** in edit mode, open **Work** and click **+ Add project**. The new project page opens so you can fill it in.
- **Social projects** (for example Porsche, BMW): the **Social** page lists them like the Work page, and each one opens its own page of posts. In edit mode, click **+ Add social project**; its page opens so you can set the name, year, description and account link, then click **+ Add post** for each post. The **Project: … ⟳** button under a post moves it to another project.

## Story highlights

Each social project page can show Instagram-style story highlights (round covers under the description). In edit mode, on a social project page, click **+ Add story highlight**, give it a title, then **+ Add story** for each story (photo or video, ideally 9:16). Visitors tap a highlight to play its stories full-screen. A highlight with no stories but with an Instagram highlight link opens that link instead.

## Add or update your CV

In the repo, click **Add file → Upload files**, drop in your CV PDF renamed to `cv.pdf`, and click **Commit changes**. Uploading a new `cv.pdf` later replaces the old one.

**Discard draft** throws away your browser draft and goes back to what is published.

Tip: compress large photos before uploading (under ~1 MB each is ideal) so the site loads fast.
