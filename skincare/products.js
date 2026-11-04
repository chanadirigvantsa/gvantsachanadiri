// ─────────────────────────────────────────────────────────────
// MY SKINCARE SHELF: edit this file to update the page.
//
// Each product looks like this:
//   {
//     routine: "morning",          // "morning", "evening" or "weekly"
//     step: "Cleanser",            // what it is (Cleanser, Serum, SPF, Mask…)
//     brand: "Brand",
//     name: "Product name",
//     why: "Why I love it, in a sentence or two.",
//     link: "https://…",           // where to buy (optional, use "" for none)
//     image: "images/file.jpg",    // photo in skincare/images/ (optional, use "" for none)
//     favourite: true              // optional: shows a ★ "Holy grail" tag
//   },
//
// The order here is the order on the page.
// Delete the example products below and put your own in.
// ─────────────────────────────────────────────────────────────

window.SKINCARE = {
  title: "My skincare shelf",
  intro: "Everything I actually use, because you keep asking. Morning, evening and the extras.",
  skinType: "Combination, a little sensitive",   // shown under the intro ("" to hide)
  updated: "November 2026",                     // shown in the footer ("" to hide)

  products: [
    // ── Morning ───────────────────────────────
    {
      routine: "morning",
      step: "Cleanser",
      brand: "Brand",
      name: "Gentle gel cleanser",
      why: "Example: replace with your product. Soft, doesn't leave my skin tight.",
      link: "",
      image: "",
      favourite: false
    },
    {
      routine: "morning",
      step: "Serum",
      brand: "Brand",
      name: "Vitamin C serum",
      why: "Example: replace with your product.",
      link: "",
      image: "",
      favourite: true
    },
    {
      routine: "morning",
      step: "Moisturiser",
      brand: "Brand",
      name: "Daily moisturiser",
      why: "Example: replace with your product.",
      link: "",
      image: "",
      favourite: false
    },
    {
      routine: "morning",
      step: "SPF",
      brand: "Brand",
      name: "Sunscreen SPF 50",
      why: "Example: replace with your product. Every day, even in winter.",
      link: "",
      image: "",
      favourite: false
    },

    // ── Evening ───────────────────────────────
    {
      routine: "evening",
      step: "Makeup remover",
      brand: "Brand",
      name: "Cleansing balm",
      why: "Example: replace with your product.",
      link: "",
      image: "",
      favourite: false
    },
    {
      routine: "evening",
      step: "Treatment",
      brand: "Brand",
      name: "Retinol serum",
      why: "Example: replace with your product. Two or three nights a week.",
      link: "",
      image: "",
      favourite: false
    },
    {
      routine: "evening",
      step: "Night cream",
      brand: "Brand",
      name: "Night cream",
      why: "Example: replace with your product.",
      link: "",
      image: "",
      favourite: false
    },

    // ── Weekly / extras ───────────────────────
    {
      routine: "weekly",
      step: "Mask",
      brand: "Brand",
      name: "Hydrating sheet mask",
      why: "Example: replace with your product.",
      link: "",
      image: "",
      favourite: false
    }
  ]
};
