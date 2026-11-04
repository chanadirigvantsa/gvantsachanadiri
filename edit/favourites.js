// ─────────────────────────────────────────────────────────────
// MY SKIN & STYLE EDIT: edit this file to update the page.
// The order in each list is the order on the page.
// Delete the examples and put your own in.
// ─────────────────────────────────────────────────────────────

window.EDIT = {
  title: "Skin & Style",
  intro: "Everything I actually use and wear, because you keep asking. My skincare routine, plus the clothes, shoe and bag brands I love.",
  skinType: "Combination, a little sensitive",   // shown on the cover ("" to hide)
  updated: "November 2026",                     // shown at the top and in the footer ("" to hide)

  // ── PART ONE: SKINCARE ─────────────────────────────────────
  // Each product:
  //   routine:   "morning", "evening" or "weekly"
  //   step:      what it is (Cleanser, Serum, SPF, Mask…)
  //   brand, name
  //   why:       why you love it, a sentence or two
  //   link:      where to buy (optional, "" for none)
  //   image:     photo in edit/images/, e.g. "images/serum.jpg" (optional)
  //   favourite: true adds a pink "Holy grail" sticker
  skincare: [
    { routine: "morning", step: "Cleanser",    brand: "Brand", name: "Gentle gel cleanser", why: "Example: replace with your product. Soft, doesn't leave my skin tight.", link: "", image: "", favourite: false },
    { routine: "morning", step: "Serum",       brand: "Brand", name: "Vitamin C serum",     why: "Example: replace with your product.", link: "", image: "", favourite: true },
    { routine: "morning", step: "Moisturiser", brand: "Brand", name: "Daily moisturiser",   why: "Example: replace with your product.", link: "", image: "", favourite: false },
    { routine: "morning", step: "SPF",         brand: "Brand", name: "Sunscreen SPF 50",    why: "Example: replace with your product. Every day, even in winter.", link: "", image: "", favourite: false },

    { routine: "evening", step: "Makeup remover", brand: "Brand", name: "Cleansing balm", why: "Example: replace with your product.", link: "", image: "", favourite: false },
    { routine: "evening", step: "Treatment",      brand: "Brand", name: "Retinol serum",  why: "Example: replace with your product. Two or three nights a week.", link: "", image: "", favourite: false },
    { routine: "evening", step: "Night cream",    brand: "Brand", name: "Night cream",    why: "Example: replace with your product.", link: "", image: "", favourite: false },

    { routine: "weekly", step: "Mask", brand: "Brand", name: "Hydrating sheet mask", why: "Example: replace with your product.", link: "", image: "", favourite: false }
  ],

  // ── PART TWO: FASHION ──────────────────────────────────────
  // Each brand:
  //   category:  "clothes", "shoes", "bags" or "accessories"
  //   brand:     the brand name
  //   piece:     what you buy from them / your favourite piece (optional)
  //   why:       why you love them, a sentence or two
  //   link:      the brand's website or shop (optional, "" for none)
  //   image:     photo in edit/images/ (optional)
  //   favourite: true adds a pink "Obsessed" sticker
  fashion: [
    { category: "clothes", brand: "Clothing brand", piece: "Tailored trousers", why: "Example: replace with your brand. The fit is perfect every time.", link: "", image: "", favourite: true },
    { category: "clothes", brand: "Clothing brand", piece: "Knitwear",          why: "Example: replace with your brand.", link: "", image: "", favourite: false },
    { category: "clothes", brand: "Clothing brand", piece: "Everyday basics",   why: "Example: replace with your brand.", link: "", image: "", favourite: false },

    { category: "shoes", brand: "Shoe brand", piece: "Ballet flats", why: "Example: replace with your brand. Comfortable from day one.", link: "", image: "", favourite: false },
    { category: "shoes", brand: "Shoe brand", piece: "Sneakers",     why: "Example: replace with your brand.", link: "", image: "", favourite: false },

    { category: "bags", brand: "Bag brand", piece: "Everyday tote", why: "Example: replace with your brand. Fits my laptop and still looks chic.", link: "", image: "", favourite: true },
    { category: "bags", brand: "Bag brand", piece: "Evening bag",   why: "Example: replace with your brand.", link: "", image: "", favourite: false }
  ]
};
