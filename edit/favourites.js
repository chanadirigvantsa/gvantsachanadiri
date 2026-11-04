// ─────────────────────────────────────────────────────────────
// MY SKIN & STYLE EDIT: edit this file to update the page.
// The order in each list is the order on the page.
// Delete the examples and put your own in.
// ─────────────────────────────────────────────────────────────

window.EDIT = {
  title: "Skin & Style",
  intro: "Because you keep asking: the skincare, clothes, shoe and bag brands I love.",
  skinType: "",   // e.g. "Combination, a little sensitive" (shown on the cover, "" to hide)
  updated: "November 2026",                     // shown at the top and in the footer ("" to hide)

  // ── PART ONE: SKINCARE ─────────────────────────────────────
  // Each brand:
  //   brand:     the brand name
  //   why:       why you love it, a sentence or two (optional)
  //   link:      where to buy (optional, "" for none)
  //   image:     photo in edit/images/, e.g. "images/serum.jpg" (optional)
  //   favourite: true adds a "Holy grail" sticker
  skincare: [
    { brand: "La Roche-Posay", why: "", link: "", image: "", favourite: false },
    { brand: "Anua", why: "", link: "", image: "", favourite: false },
    { brand: "Beauty of Joseon", why: "", link: "", image: "", favourite: false },
    { brand: "SkinCeuticals", why: "", link: "", image: "", favourite: false },
    { brand: "K-Secret", why: "", link: "", image: "", favourite: false }
  ],

  // ── PART TWO: FASHION ──────────────────────────────────────
  // Each brand:
  //   category:  "clothes", "shoes", "bags" or "accessories"
  //   brand:     the brand name
  //   why:       why you love them, a sentence or two
  //   link:      the brand's website or shop (optional, "" for none)
  //   image:     photo in edit/images/ (optional)
  //   favourite: true adds a pink "Obsessed" sticker
  fashion: [
    { category: "clothes", brand: "Clothing brand", why: "Example: replace with your brand.", link: "", image: "", favourite: true },
    { category: "clothes", brand: "Clothing brand",          why: "Example: replace with your brand.", link: "", image: "", favourite: false },
    { category: "clothes", brand: "Clothing brand",   why: "Example: replace with your brand.", link: "", image: "", favourite: false },

    { category: "shoes", brand: "Shoe brand", why: "Example: replace with your brand.", link: "", image: "", favourite: false },
    { category: "shoes", brand: "Shoe brand",     why: "Example: replace with your brand.", link: "", image: "", favourite: false },

    { category: "bags", brand: "Bag brand", why: "Example: replace with your brand.", link: "", image: "", favourite: true },
    { category: "bags", brand: "Bag brand",   why: "Example: replace with your brand.", link: "", image: "", favourite: false }
  ]
};
