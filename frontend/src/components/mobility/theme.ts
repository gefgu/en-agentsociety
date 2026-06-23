export const LIGHT_PALETTE = {
  bg:        "#fbf8f1",
  grid:      "#dcd5c4",
  axis:      "#14110d",
  observed:  "#14110d",
  synthetic: "#c8533a",
  syn2:      "#7a8c5a",
  syn3:      "#3d6a8a",
  baseline:  "#a39c8e",
  muted:     "#6b5e4c",
  border:    "#dcd5c4",
  panel:     "#fffdf8",
};

export const DARK_PALETTE = {
  bg:        "#0c1728",
  grid:      "rgba(255,255,255,0.07)",
  axis:      "#c9d8ee",
  observed:  "#c9d8ee",
  synthetic: "#e07b64",
  syn2:      "#98b870",
  syn3:      "#6aaed6",
  baseline:  "#6e7a8a",
  muted:     "#7a91aa",
  border:    "rgba(255,255,255,0.09)",
  panel:     "#0d1829",
};

export const getPalette = (theme: 'dark' | 'light') =>
  theme === 'dark' ? DARK_PALETTE : LIGHT_PALETTE;

// Keep backward-compat alias for files that haven't migrated yet.
export const PALETTE = DARK_PALETTE;

export const FONT_SERIF = '"Space Grotesk", Georgia, serif';
export const FONT_SANS = '"DM Sans", system-ui, sans-serif';
export const FONT_MONO = '"JetBrains Mono", ui-monospace, "SFMono-Regular", monospace';
