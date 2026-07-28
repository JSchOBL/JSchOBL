#!/usr/bin/env python3
"""Render the static chrome for the profile README: section headers and buttons.

They mirror the `01. About Me` headings and the outlined call-to-action buttons
on johannes-schieder.com. Each one is a self-contained navy panel, so it looks
identical in GitHub's light and dark theme instead of vanishing against a white
background.

    python3 scripts/generate_decor.py
"""

from __future__ import annotations

import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets")

SECTIONS = [
    ("01", "About Me", "about"),
    ("02", "Where I've Worked", "experience"),
    ("03", "Some Things I've Built", "projects"),
    ("04", "By The Numbers", "stats"),
    ("05", "Get In Touch", "contact"),
]

BUTTONS = [
    ("All Repositories ↗", "btn-repos"),
]

W, H = 900, 50
MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"
     viewBox="0 0 {w} {h}" role="img" aria-label="{number}. {label}">
  <title>{number}. {label}</title>
  <defs>
    <linearGradient id="fade" x1="0" x2="1">
      <stop offset="0%" stop-color="#233554"/>
      <stop offset="100%" stop-color="#233554" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="sweep" x1="0" x2="1">
      <stop offset="0%" stop-color="#64ffda" stop-opacity="0"/>
      <stop offset="50%" stop-color="#64ffda" stop-opacity=".7"/>
      <stop offset="100%" stop-color="#64ffda" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate"
                        values="-1 0; 1 0; 1 0" dur="6s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>
  <rect x=".5" y=".5" width="{w1}" height="{h1}" rx="8" fill="#0a192f" stroke="#233554"/>
  <rect x="20" y="13" width="3" height="24" rx="1.5" fill="#64ffda"/>
  <text x="36" y="32" font-family="{mono}" font-size="15" fill="#64ffda">{number}.</text>
  <text x="{label_x}" y="32" font-family="{sans}" font-size="19" font-weight="600"
        letter-spacing="-.2" fill="#ccd6f6">{label}</text>
  <rect x="{line_x}" y="24.5" width="{line_w}" height="1" fill="url(#fade)"/>
  <rect x="{line_x}" y="24.5" width="{line_w}" height="1" fill="url(#sweep)"/>
</svg>
"""


BUTTON = """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="46"
     viewBox="0 0 {w} 46" role="img" aria-label="{label}">
  <title>{label}</title>
  <style>
    @keyframes pulse {{ 0%,100% {{ opacity: .07 }} 50% {{ opacity: .16 }} }}
    .fill {{ animation: pulse 3.2s ease-in-out infinite; }}
    @media (prefers-reduced-motion: reduce) {{ .fill {{ animation: none }} }}
  </style>
  <rect x=".75" y=".75" width="{w1}" height="44.5" rx="5" fill="#0a192f" stroke="#64ffda"
        stroke-width="1.5"/>
  <rect class="fill" x=".75" y=".75" width="{w1}" height="44.5" rx="5" fill="#64ffda"/>
  <text x="{cx}" y="28.5" text-anchor="middle" font-family="{mono}" font-size="13.5"
        letter-spacing=".3" fill="#64ffda">{label}</text>
</svg>
"""


def main() -> None:
    os.makedirs(OUT, exist_ok=True)

    for label, slug in BUTTONS:
        width = round(8.15 * len(label) + 56)
        svg = BUTTON.format(w=width, w1=width - 1.5, cx=width / 2, mono=MONO,
                            label=label.replace("&", "&amp;"))
        with open(os.path.join(OUT, f"{slug}.svg"), "w", encoding="utf-8") as handle:
            handle.write(svg)
        print(f"  wrote assets/{slug}.svg")

    for number, label, slug in SECTIONS:
        label_x = 36 + 9.1 * len(number + ".") + 12
        line_x = label_x + 10.4 * len(label) + 18
        svg = TEMPLATE.format(
            w=W, h=H, w1=W - 1, h1=H - 1, mono=MONO, sans=SANS,
            number=number, label=label.replace("'", "&#39;"),
            label_x=f"{label_x:.1f}", line_x=f"{line_x:.1f}",
            line_w=f"{W - 24 - line_x:.1f}",
        )
        path = os.path.join(OUT, f"h-{slug}.svg")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(svg)
        print(f"  wrote assets/h-{slug}.svg")


if __name__ == "__main__":
    main()
