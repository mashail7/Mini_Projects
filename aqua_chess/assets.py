"""
assets.py – Embedded SVG chess pieces, QSS stylesheet, and color constants
for the "Aqua Chess" application (Beach & Ocean theme).

All 12 SVG chess pieces (6 types × 2 colors) use viewBox="0 0 64 64"
and are rendered as luxury marine-themed artifacts with multi-layer gradients,
offset shadow paths, specular highlights, and carved nautical details.

No external dependencies beyond the `chess` library (for piece-type constants).
"""

import chess

# ---------------------------------------------------------------------------
# 1. SVG Chess Pieces  (12 total: 6 piece types × 2 colors)
# ---------------------------------------------------------------------------
# White pieces: "Sunlit Mother-of-Pearl & Royal Gold"
#   Multi-stop radial/linear gradients: pearl white #FFFDF9 → seashell ivory
#   #F3E5AB → champagne sand #D6C29F, gold trim #D4AF37, dark bronze outlines #4A3B2C
#
# Black pieces: "Abyssal Obsidian & Bioluminescent Coral"
#   Deep ocean gradients: midnight teal #071A24 → marine slate #133B4E →
#   turquoise rim #2A9D8F, coral-gold trim #E76F51 / #F4A261, luminous cyan #80FFDB

# ── GRADIENT DEFINITIONS ──────────────────────────────────────────────────

_WHITE_DEFS = '''<defs>
  <linearGradient id="wBody" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#FFFDF9"/>
    <stop offset="35%" stop-color="#F5ECD0"/>
    <stop offset="70%" stop-color="#F3E5AB"/>
    <stop offset="100%" stop-color="#D6C29F"/>
  </linearGradient>
  <radialGradient id="wHighlight" cx="0.38" cy="0.25" r="0.55">
    <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.85"/>
    <stop offset="60%" stop-color="#FFFDF9" stop-opacity="0.25"/>
    <stop offset="100%" stop-color="#F3E5AB" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="wTrim" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#E8CB6B"/>
    <stop offset="50%" stop-color="#D4AF37"/>
    <stop offset="100%" stop-color="#B8962E"/>
  </linearGradient>
  <linearGradient id="wBase" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#F3E5AB"/>
    <stop offset="100%" stop-color="#C4A86A"/>
  </linearGradient>
  <radialGradient id="wPearl" cx="0.45" cy="0.35" r="0.5">
    <stop offset="0%" stop-color="#FFFFFF"/>
    <stop offset="40%" stop-color="#FFF8EE"/>
    <stop offset="100%" stop-color="#E8D5A8"/>
  </radialGradient>
  <linearGradient id="wShadow" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#4A3B2C" stop-opacity="0"/>
    <stop offset="100%" stop-color="#4A3B2C" stop-opacity="0.35"/>
  </linearGradient>
</defs>'''

_BLACK_DEFS = '''<defs>
  <linearGradient id="bBody" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#1A4B5E"/>
    <stop offset="35%" stop-color="#133B4E"/>
    <stop offset="70%" stop-color="#0E2D3E"/>
    <stop offset="100%" stop-color="#071A24"/>
  </linearGradient>
  <radialGradient id="bHighlight" cx="0.38" cy="0.22" r="0.50">
    <stop offset="0%" stop-color="#80FFDB" stop-opacity="0.50"/>
    <stop offset="50%" stop-color="#2A9D8F" stop-opacity="0.18"/>
    <stop offset="100%" stop-color="#071A24" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="bTrim" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#F4A261"/>
    <stop offset="50%" stop-color="#E76F51"/>
    <stop offset="100%" stop-color="#C45A3E"/>
  </linearGradient>
  <linearGradient id="bBase" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#133B4E"/>
    <stop offset="100%" stop-color="#071A24"/>
  </linearGradient>
  <radialGradient id="bPearl" cx="0.45" cy="0.35" r="0.5">
    <stop offset="0%" stop-color="#80FFDB"/>
    <stop offset="40%" stop-color="#4DD8B0"/>
    <stop offset="100%" stop-color="#2A9D8F"/>
  </radialGradient>
  <linearGradient id="bRim" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#2A9D8F"/>
    <stop offset="100%" stop-color="#1A6B60"/>
  </linearGradient>
  <linearGradient id="bShadow" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#000000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#000000" stop-opacity="0.40"/>
  </linearGradient>
</defs>'''


def _w_svg(inner: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'{_WHITE_DEFS}'
        f'{inner}'
        '</svg>'
    )


def _b_svg(inner: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'{_BLACK_DEFS}'
        f'{inner}'
        '</svg>'
    )


# ═══════════════════════════════════════════════════════════════════════════
# KING — Tall Imperial Crown & Royal Cross
# ═══════════════════════════════════════════════════════════════════════════

_KING_W = _w_svg('''
<!-- drop shadow -->
<path d="M 10 56 L 54 56 L 54 59 C 54 60 46 61 32 61 C 18 61 10 60 10 59 Z" fill="#000000" fill-opacity="0.22" transform="translate(1.2, 1.8)"/>
<!-- double pedestal base -->
<rect x="10" y="54" width="44" height="5" rx="2.5" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="1.2"/>
<path d="M 13 54 C 13 49, 51 49, 51 54 Z" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="1.1"/>
<!-- fluted pillar body -->
<path d="M 20 37 C 19 43, 17 47, 15 50 H 49 C 47 47, 45 43, 44 37 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="1.2"/>
<!-- 3 vertical gold flute lines -->
<line x1="26" y1="38" x2="26" y2="49" stroke="#D4AF37" stroke-width="1.2" stroke-linecap="round"/>
<line x1="32" y1="38" x2="32" y2="49" stroke="#D4AF37" stroke-width="1.2" stroke-linecap="round"/>
<line x1="38" y1="38" x2="38" y2="49" stroke="#D4AF37" stroke-width="1.2" stroke-linecap="round"/>
<!-- royal collar -->
<rect x="16" y="33" width="32" height="4" rx="2" fill="url(#wTrim)" stroke="#4A3B2C" stroke-width="1"/>
<!-- wide 5-peak flared imperial crown -->
<path d="M 17 33 L 11 18 L 21.5 24.5 L 32 15 L 42.5 24.5 L 53 18 L 47 33 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="1.2" stroke-linejoin="round"/>
<!-- crown jewels (pearl gems) -->
<circle cx="22" cy="29" r="2.2" fill="url(#wPearl)" stroke="#D4AF37" stroke-width="0.7"/>
<circle cx="32" cy="28" r="2.6" fill="url(#wPearl)" stroke="#D4AF37" stroke-width="0.7"/>
<circle cx="42" cy="29" r="2.2" fill="url(#wPearl)" stroke="#D4AF37" stroke-width="0.7"/>
<!-- prominent royal cross at the top -->
<path d="M 29.5 3 H 34.5 V 7.5 H 39 V 12 H 34.5 V 16 H 29.5 V 12 H 25 V 7.5 H 29.5 Z" fill="url(#wTrim)" stroke="#4A3B2C" stroke-width="1.1" stroke-linejoin="round"/>
<!-- specular highlights -->
<ellipse cx="32" cy="20" rx="3.5" ry="2" fill="url(#wHighlight)"/>
''')

_KING_B = _b_svg('''
<!-- drop shadow -->
<path d="M 10 56 L 54 56 L 54 59 C 54 60 46 61 32 61 C 18 61 10 60 10 59 Z" fill="#000000" fill-opacity="0.30" transform="translate(1.5, 2.2)"/>
<!-- double pedestal base -->
<rect x="10" y="54" width="44" height="5" rx="2.5" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="1.2"/>
<path d="M 13 54 C 13 49, 51 49, 51 54 Z" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="1.1"/>
<!-- fluted pillar body -->
<path d="M 20 37 C 19 43, 17 47, 15 50 H 49 C 47 47, 45 43, 44 37 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="1.2"/>
<!-- 3 vertical turquoise/cyan flute lines -->
<line x1="26" y1="38" x2="26" y2="49" stroke="#80FFDB" stroke-width="1.2" stroke-linecap="round"/>
<line x1="32" y1="38" x2="32" y2="49" stroke="#80FFDB" stroke-width="1.2" stroke-linecap="round"/>
<line x1="38" y1="38" x2="38" y2="49" stroke="#80FFDB" stroke-width="1.2" stroke-linecap="round"/>
<!-- royal collar -->
<rect x="16" y="33" width="32" height="4" rx="2" fill="url(#bTrim)" stroke="#2A9D8F" stroke-width="1"/>
<!-- wide 5-peak flared imperial crown -->
<path d="M 17 33 L 11 18 L 21.5 24.5 L 32 15 L 42.5 24.5 L 53 18 L 47 33 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="1.2" stroke-linejoin="round"/>
<!-- crown jewels (coral gems) -->
<circle cx="22" cy="29" r="2.2" fill="url(#bPearl)" stroke="#E76F51" stroke-width="0.7"/>
<circle cx="32" cy="28" r="2.6" fill="url(#bPearl)" stroke="#E76F51" stroke-width="0.7"/>
<circle cx="42" cy="29" r="2.2" fill="url(#bPearl)" stroke="#E76F51" stroke-width="0.7"/>
<!-- prominent royal cross at the top -->
<path d="M 29.5 3 H 34.5 V 7.5 H 39 V 12 H 34.5 V 16 H 29.5 V 12 H 25 V 7.5 H 29.5 Z" fill="url(#bTrim)" stroke="#2A9D8F" stroke-width="1.1" stroke-linejoin="round"/>
<!-- bioluminescent highlights -->
<ellipse cx="32" cy="20" rx="3.5" ry="2" fill="url(#bHighlight)"/>
''')


# ═══════════════════════════════════════════════════════════════════════════
# QUEEN — Atlantis Sea-Crown with 5 Wave-Crest Points & Pearls
# ═══════════════════════════════════════════════════════════════════════════

_QUEEN_W = _w_svg('''
<!-- drop shadow -->
<path d="M 16 56 C 16 58 22 60 32 60 C 42 60 48 58 48 56 L 48 50 C 48 48 42 46 32 46 C 22 46 16 48 16 50 Z" fill="#000000" fill-opacity="0.20" transform="translate(1.2, 1.5)"/>
<!-- fluted shell base -->
<path d="M 15 55 C 15 57 21 59 32 59 C 43 59 49 57 49 55 L 49 52 C 49 50 43 48 32 48 C 21 48 15 50 15 52 Z" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="1.1"/>
<path d="M 17 52 Q 20 49 24 52 Q 27 49 30 52 Q 33 49 36 52 Q 39 49 42 52 Q 45 49 47 52" fill="none" stroke="#D4AF37" stroke-width="0.7"/>
<!-- mermaid-scale hourglass body -->
<path d="M 23 48 C 23 44 25 42 27 40 C 28 38 28 36 28 34 L 36 34 C 36 36 36 38 37 40 C 39 42 41 44 41 48 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="1.1"/>
<!-- scale texture -->
<path d="M 28 42 Q 30 40 32 42 Q 34 44 36 42" fill="none" stroke="#D4AF37" stroke-width="0.5" stroke-opacity="0.5"/>
<path d="M 27 45 Q 30 43 32 45 Q 34 47 37 45" fill="none" stroke="#D4AF37" stroke-width="0.5" stroke-opacity="0.4"/>
<!-- decorative collar -->
<ellipse cx="32" cy="34" rx="8" ry="2.5" fill="url(#wTrim)" stroke="#4A3B2C" stroke-width="0.7"/>
<!-- crown body connecting to 5 wave-crest points -->
<path d="M 24 34 C 24 28 20 22 14 18 L 18 28 L 21 20 L 26 30 L 32 14 L 38 30 L 43 20 L 46 28 L 50 18 C 44 22 40 28 40 34 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="1"/>
<!-- 5 glowing pearls on wave crests -->
<circle cx="14" cy="17" r="2.2" fill="url(#wPearl)" stroke="#D4AF37" stroke-width="0.6"/>
<circle cx="21" cy="19" r="2" fill="url(#wPearl)" stroke="#D4AF37" stroke-width="0.6"/>
<circle cx="32" cy="13" r="2.5" fill="url(#wPearl)" stroke="#D4AF37" stroke-width="0.6"/>
<circle cx="43" cy="19" r="2" fill="url(#wPearl)" stroke="#D4AF37" stroke-width="0.6"/>
<circle cx="50" cy="17" r="2.2" fill="url(#wPearl)" stroke="#D4AF37" stroke-width="0.6"/>
<!-- specular highlight on crown -->
<path d="M 28 22 C 28 20 30 16 32 16 C 34 16 36 20 36 22 C 36 26 34 28 32 28 C 30 28 28 26 28 22 Z" fill="url(#wHighlight)"/>
<!-- inner rim -->
<path d="M 24 34 C 24 28 20 22 14 18" fill="none" stroke="#FFFDF9" stroke-width="0.5" stroke-opacity="0.4"/>
<path d="M 40 34 C 40 28 44 22 50 18" fill="none" stroke="#FFFDF9" stroke-width="0.5" stroke-opacity="0.4"/>
''')

_QUEEN_B = _b_svg('''
<!-- drop shadow -->
<path d="M 16 56 C 16 58 22 60 32 60 C 42 60 48 58 48 56 L 48 50 C 48 48 42 46 32 46 C 22 46 16 48 16 50 Z" fill="#000000" fill-opacity="0.28" transform="translate(1.5, 2)"/>
<!-- shell base -->
<path d="M 15 55 C 15 57 21 59 32 59 C 43 59 49 57 49 55 L 49 52 C 49 50 43 48 32 48 C 21 48 15 50 15 52 Z" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="1.1"/>
<path d="M 17 52 Q 20 49 24 52 Q 27 49 30 52 Q 33 49 36 52 Q 39 49 42 52 Q 45 49 47 52" fill="none" stroke="#F4A261" stroke-width="0.7"/>
<!-- body -->
<path d="M 23 48 C 23 44 25 42 27 40 C 28 38 28 36 28 34 L 36 34 C 36 36 36 38 37 40 C 39 42 41 44 41 48 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="1.1"/>
<!-- scale texture -->
<path d="M 28 42 Q 30 40 32 42 Q 34 44 36 42" fill="none" stroke="#F4A261" stroke-width="0.5" stroke-opacity="0.45"/>
<path d="M 27 45 Q 30 43 32 45 Q 34 47 37 45" fill="none" stroke="#F4A261" stroke-width="0.5" stroke-opacity="0.35"/>
<!-- collar -->
<ellipse cx="32" cy="34" rx="8" ry="2.5" fill="url(#bTrim)" stroke="#2A9D8F" stroke-width="0.7"/>
<!-- crown body -->
<path d="M 24 34 C 24 28 20 22 14 18 L 18 28 L 21 20 L 26 30 L 32 14 L 38 30 L 43 20 L 46 28 L 50 18 C 44 22 40 28 40 34 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="1"/>
<!-- glowing pearls -->
<circle cx="14" cy="17" r="2.2" fill="url(#bPearl)" stroke="#E76F51" stroke-width="0.6"/>
<circle cx="21" cy="19" r="2" fill="url(#bPearl)" stroke="#E76F51" stroke-width="0.6"/>
<circle cx="32" cy="13" r="2.5" fill="url(#bPearl)" stroke="#E76F51" stroke-width="0.6"/>
<circle cx="43" cy="19" r="2" fill="url(#bPearl)" stroke="#E76F51" stroke-width="0.6"/>
<circle cx="50" cy="17" r="2.2" fill="url(#bPearl)" stroke="#E76F51" stroke-width="0.6"/>
<!-- bioluminescent highlight -->
<path d="M 28 22 C 28 20 30 16 32 16 C 34 16 36 20 36 22 C 36 26 34 28 32 28 C 30 28 28 26 28 22 Z" fill="url(#bHighlight)"/>
<!-- turquoise rim accents -->
<path d="M 24 34 C 24 28 20 22 14 18" fill="none" stroke="#80FFDB" stroke-width="0.5" stroke-opacity="0.35"/>
<path d="M 40 34 C 40 28 44 22 50 18" fill="none" stroke="#80FFDB" stroke-width="0.5" stroke-opacity="0.35"/>
''')


# ═══════════════════════════════════════════════════════════════════════════
# ROOK — Coastal Lighthouse & Atlantis Fortress Tower
# ═══════════════════════════════════════════════════════════════════════════

_ROOK_W = _w_svg('''
<!-- drop shadow -->
<path d="M 14 55 L 50 55 L 50 58 C 50 59 46 60 32 60 C 18 60 14 59 14 58 Z" fill="#000000" fill-opacity="0.20" transform="translate(1.2, 1.5)"/>
<!-- reef-rock base -->
<path d="M 13 55 L 51 55 L 51 50 L 13 50 Z" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="1.1"/>
<path d="M 11 58 L 53 58 L 53 55 L 11 55 Z" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="1.2"/>
<!-- base texture -->
<line x1="16" y1="57" x2="48" y2="57" stroke="#D4AF37" stroke-width="0.5" stroke-opacity="0.5"/>
<!-- tower body with stone masonry blocks -->
<path d="M 18 50 L 18 22 L 46 22 L 46 50 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="1.1"/>
<!-- masonry block lines -->
<line x1="18" y1="28" x2="46" y2="28" stroke="#4A3B2C" stroke-width="0.4" stroke-opacity="0.35"/>
<line x1="18" y1="34" x2="46" y2="34" stroke="#4A3B2C" stroke-width="0.4" stroke-opacity="0.35"/>
<line x1="18" y1="40" x2="46" y2="40" stroke="#4A3B2C" stroke-width="0.4" stroke-opacity="0.35"/>
<line x1="18" y1="46" x2="46" y2="46" stroke="#4A3B2C" stroke-width="0.4" stroke-opacity="0.35"/>
<line x1="32" y1="22" x2="32" y2="28" stroke="#4A3B2C" stroke-width="0.4" stroke-opacity="0.25"/>
<line x1="25" y1="28" x2="25" y2="34" stroke="#4A3B2C" stroke-width="0.4" stroke-opacity="0.25"/>
<line x1="39" y1="28" x2="39" y2="34" stroke="#4A3B2C" stroke-width="0.4" stroke-opacity="0.25"/>
<line x1="32" y1="34" x2="32" y2="40" stroke="#4A3B2C" stroke-width="0.4" stroke-opacity="0.25"/>
<!-- arched lookout window with lantern glow -->
<path d="M 28 32 C 28 27 32 25 36 27 L 36 34 L 28 34 Z" fill="#F5ECD0" fill-opacity="0.6" stroke="#D4AF37" stroke-width="0.7"/>
<ellipse cx="32" cy="30" rx="2.5" ry="2.5" fill="#FFFDF9" fill-opacity="0.7"/>
<!-- wave-guard battlements -->
<path d="M 14 22 L 14 14 L 20 14 L 20 18 L 24 18 L 24 14 L 30 14 L 30 18 L 34 18 L 34 14 L 40 14 L 40 18 L 44 18 L 44 14 L 50 14 L 50 22 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="1"/>
<!-- battlement wave accent -->
<path d="M 16 16 Q 19 13 22 16 Q 25 13 28 16 Q 31 13 34 16 Q 37 13 40 16 Q 43 13 46 16" fill="none" stroke="#D4AF37" stroke-width="0.6" stroke-opacity="0.55"/>
<!-- gold trim lines -->
<line x1="14" y1="22" x2="50" y2="22" stroke="#D4AF37" stroke-width="0.8"/>
<!-- specular highlight -->
<rect x="20" y="24" width="6" height="24" rx="3" fill="url(#wHighlight)" fill-opacity="0.5"/>
''')

_ROOK_B = _b_svg('''
<!-- drop shadow -->
<path d="M 14 55 L 50 55 L 50 58 C 50 59 46 60 32 60 C 18 60 14 59 14 58 Z" fill="#000000" fill-opacity="0.28" transform="translate(1.5, 2)"/>
<!-- base -->
<path d="M 13 55 L 51 55 L 51 50 L 13 50 Z" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="1.1"/>
<path d="M 11 58 L 53 58 L 53 55 L 11 55 Z" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="1.2"/>
<line x1="16" y1="57" x2="48" y2="57" stroke="#F4A261" stroke-width="0.5" stroke-opacity="0.45"/>
<!-- tower body -->
<path d="M 18 50 L 18 22 L 46 22 L 46 50 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="1.1"/>
<!-- masonry -->
<line x1="18" y1="28" x2="46" y2="28" stroke="#2A9D8F" stroke-width="0.4" stroke-opacity="0.35"/>
<line x1="18" y1="34" x2="46" y2="34" stroke="#2A9D8F" stroke-width="0.4" stroke-opacity="0.35"/>
<line x1="18" y1="40" x2="46" y2="40" stroke="#2A9D8F" stroke-width="0.4" stroke-opacity="0.35"/>
<line x1="18" y1="46" x2="46" y2="46" stroke="#2A9D8F" stroke-width="0.4" stroke-opacity="0.35"/>
<line x1="32" y1="22" x2="32" y2="28" stroke="#2A9D8F" stroke-width="0.4" stroke-opacity="0.2"/>
<line x1="25" y1="28" x2="25" y2="34" stroke="#2A9D8F" stroke-width="0.4" stroke-opacity="0.2"/>
<line x1="39" y1="28" x2="39" y2="34" stroke="#2A9D8F" stroke-width="0.4" stroke-opacity="0.2"/>
<line x1="32" y1="34" x2="32" y2="40" stroke="#2A9D8F" stroke-width="0.4" stroke-opacity="0.2"/>
<!-- window with bioluminescent glow -->
<path d="M 28 32 C 28 27 32 25 36 27 L 36 34 L 28 34 Z" fill="#133B4E" fill-opacity="0.7" stroke="#E76F51" stroke-width="0.7"/>
<ellipse cx="32" cy="30" rx="2.5" ry="2.5" fill="#80FFDB" fill-opacity="0.55"/>
<!-- battlements -->
<path d="M 14 22 L 14 14 L 20 14 L 20 18 L 24 18 L 24 14 L 30 14 L 30 18 L 34 18 L 34 14 L 40 14 L 40 18 L 44 18 L 44 14 L 50 14 L 50 22 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="1"/>
<!-- wave accent -->
<path d="M 16 16 Q 19 13 22 16 Q 25 13 28 16 Q 31 13 34 16 Q 37 13 40 16 Q 43 13 46 16" fill="none" stroke="#F4A261" stroke-width="0.6" stroke-opacity="0.5"/>
<!-- coral trim -->
<line x1="14" y1="22" x2="50" y2="22" stroke="#E76F51" stroke-width="0.8"/>
<!-- highlight -->
<rect x="20" y="24" width="6" height="24" rx="3" fill="url(#bHighlight)" fill-opacity="0.45"/>
''')


# ═══════════════════════════════════════════════════════════════════════════
# BISHOP — Conch & Nautilus Mitre with Golden Spiral Emblem
# ═══════════════════════════════════════════════════════════════════════════

_BISHOP_W = _w_svg('''
<!-- drop shadow -->
<path d="M 17 56 C 17 58 22 60 32 60 C 42 60 47 58 47 56 L 47 52 C 47 50 42 48 32 48 C 22 48 17 50 17 52 Z" fill="#000000" fill-opacity="0.20" transform="translate(1.2, 1.5)"/>
<!-- tiered base -->
<path d="M 15 56 C 15 58 22 59 32 59 C 42 59 49 58 49 56 L 49 53 C 49 51 42 50 32 50 C 22 50 15 51 15 53 Z" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="1.1"/>
<path d="M 18 53 L 46 53 L 46 50 L 18 50 Z" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="0.8"/>
<!-- polished collar -->
<path d="M 20 50 C 20 48 24 46 32 46 C 40 46 44 48 44 50 Z" fill="url(#wTrim)" stroke="#4A3B2C" stroke-width="0.8"/>
<!-- diagonal wave sash -->
<path d="M 26 46 L 38 30" stroke="#D4AF37" stroke-width="1" stroke-opacity="0.55" stroke-linecap="round"/>
<!-- mitre (conch-nautilus shape) -->
<path d="M 32 8 C 22 12 18 20 18 30 C 18 38 22 44 26 46 L 38 46 C 42 44 46 38 46 30 C 46 20 42 12 32 8 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="1.2"/>
<!-- golden nautilus spiral emblem -->
<path d="M 32 26 C 30 24 28 26 28 28 C 28 31 30 33 33 33 C 37 33 39 30 39 26 C 39 21 36 18 32 18 C 26 18 23 22 23 28 C 23 35 27 39 33 39" fill="none" stroke="#D4AF37" stroke-width="1" stroke-linecap="round"/>
<!-- pearl center of spiral -->
<circle cx="32" cy="28" r="2" fill="url(#wPearl)" stroke="#D4AF37" stroke-width="0.5"/>
<!-- finial ball -->
<circle cx="32" cy="7" r="2.8" fill="url(#wPearl)" stroke="#4A3B2C" stroke-width="0.9"/>
<!-- specular highlight -->
<path d="M 26 14 C 26 12 29 10 32 10 C 35 10 38 14 36 18 C 34 22 28 20 26 14 Z" fill="url(#wHighlight)"/>
<!-- inner rim -->
<path d="M 32 8 C 22 12 18 20 18 30 C 18 38 22 44 26 46" fill="none" stroke="#FFFDF9" stroke-width="0.5" stroke-opacity="0.4"/>
''')

_BISHOP_B = _b_svg('''
<!-- drop shadow -->
<path d="M 17 56 C 17 58 22 60 32 60 C 42 60 47 58 47 56 L 47 52 C 47 50 42 48 32 48 C 22 48 17 50 17 52 Z" fill="#000000" fill-opacity="0.28" transform="translate(1.5, 2)"/>
<!-- tiered base -->
<path d="M 15 56 C 15 58 22 59 32 59 C 42 59 49 58 49 56 L 49 53 C 49 51 42 50 32 50 C 22 50 15 51 15 53 Z" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="1.1"/>
<path d="M 18 53 L 46 53 L 46 50 L 18 50 Z" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="0.8"/>
<!-- collar -->
<path d="M 20 50 C 20 48 24 46 32 46 C 40 46 44 48 44 50 Z" fill="url(#bTrim)" stroke="#2A9D8F" stroke-width="0.8"/>
<!-- sash -->
<path d="M 26 46 L 38 30" stroke="#F4A261" stroke-width="1" stroke-opacity="0.5" stroke-linecap="round"/>
<!-- mitre -->
<path d="M 32 8 C 22 12 18 20 18 30 C 18 38 22 44 26 46 L 38 46 C 42 44 46 38 46 30 C 46 20 42 12 32 8 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="1.2"/>
<!-- nautilus spiral -->
<path d="M 32 26 C 30 24 28 26 28 28 C 28 31 30 33 33 33 C 37 33 39 30 39 26 C 39 21 36 18 32 18 C 26 18 23 22 23 28 C 23 35 27 39 33 39" fill="none" stroke="#F4A261" stroke-width="1" stroke-linecap="round"/>
<!-- pearl -->
<circle cx="32" cy="28" r="2" fill="url(#bPearl)" stroke="#E76F51" stroke-width="0.5"/>
<!-- finial -->
<circle cx="32" cy="7" r="2.8" fill="url(#bPearl)" stroke="#2A9D8F" stroke-width="0.9"/>
<!-- highlight -->
<path d="M 26 14 C 26 12 29 10 32 10 C 35 10 38 14 36 18 C 34 22 28 20 26 14 Z" fill="url(#bHighlight)"/>
<!-- rim -->
<path d="M 32 8 C 22 12 18 20 18 30 C 18 38 22 44 26 46" fill="none" stroke="#80FFDB" stroke-width="0.5" stroke-opacity="0.35"/>
''')


# ═══════════════════════════════════════════════════════════════════════════
# KNIGHT — Classic Horse Head Profile
# ═══════════════════════════════════════════════════════════════════════════

_KNIGHT_W = _w_svg('''
<!-- drop shadow -->
<path d="M 12 55 L 52 55 L 52 58 C 52 59 46 60 32 60 C 18 60 12 59 12 58 Z" fill="#000000" fill-opacity="0.20" transform="translate(1.2, 1.5)"/>
<!-- pedestal base -->
<rect x="12" y="54" width="40" height="5" rx="2.5" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="1.2"/>
<path d="M 16 54 C 16 49, 48 49, 48 54 Z" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="1.1"/>
<rect x="18" y="47" width="28" height="3.5" rx="1.7" fill="url(#wTrim)" stroke="#4A3B2C" stroke-width="0.8"/>
<!-- main horse head, pointed ears, long muzzle & muscular neck -->
<path d="M 19 47 C 18 39, 21 33, 26 29 L 17 31 C 12 31, 10 28, 11 24 L 9 22 C 9 18, 15 15, 22 13 L 23 6 L 28 12 L 33 5 L 35 12 C 45 14, 50 23, 49 35 C 48 41, 46 44, 45 47 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="1.2" stroke-linejoin="round"/>
<!-- sculpted flowing wave-mane -->
<path d="M 35 12 C 44 15, 48 22, 43 25 C 49 27, 49 33, 44 36 C 48 38, 48 43, 45 47 L 40 47 C 42 40, 41 25, 34 14 Z" fill="url(#wTrim)" stroke="#4A3B2C" stroke-width="1" stroke-linejoin="round"/>
<!-- facial details -->
<circle cx="22" cy="18.5" r="2.2" fill="#4A3B2C" stroke="#D4AF37" stroke-width="0.6"/>
<circle cx="21.3" cy="17.8" r="0.8" fill="#FFFFFF"/>
<circle cx="13.5" cy="22.5" r="1.4" fill="#4A3B2C"/>
<path d="M 11 26.5 Q 17 27 22 24.5" fill="none" stroke="#4A3B2C" stroke-width="1.8" stroke-linecap="round"/>
<!-- neck muscle & mane highlights -->
<path d="M 26 29 Q 31 36 28 46" fill="none" stroke="#D4AF37" stroke-width="1.5" stroke-linecap="round"/>
<path d="M 23 15 C 26 17, 30 20, 27 26" fill="none" stroke="#FFFDF9" stroke-width="1.2" stroke-linecap="round" stroke-opacity="0.7"/>
''')

_KNIGHT_B = _b_svg('''
<!-- drop shadow -->
<path d="M 12 55 L 52 55 L 52 58 C 52 59 46 60 32 60 C 18 60 12 59 12 58 Z" fill="#000000" fill-opacity="0.28" transform="translate(1.5, 2)"/>
<!-- pedestal base -->
<rect x="12" y="54" width="40" height="5" rx="2.5" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="1.2"/>
<path d="M 16 54 C 16 49, 48 49, 48 54 Z" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="1.1"/>
<rect x="18" y="47" width="28" height="3.5" rx="1.7" fill="url(#bTrim)" stroke="#2A9D8F" stroke-width="0.8"/>
<!-- main horse head, pointed ears, long muzzle & muscular neck -->
<path d="M 19 47 C 18 39, 21 33, 26 29 L 17 31 C 12 31, 10 28, 11 24 L 9 22 C 9 18, 15 15, 22 13 L 23 6 L 28 12 L 33 5 L 35 12 C 45 14, 50 23, 49 35 C 48 41, 46 44, 45 47 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="1.2" stroke-linejoin="round"/>
<!-- sculpted flowing wave-mane -->
<path d="M 35 12 C 44 15, 48 22, 43 25 C 49 27, 49 33, 44 36 C 48 38, 48 43, 45 47 L 40 47 C 42 40, 41 25, 34 14 Z" fill="url(#bTrim)" stroke="#2A9D8F" stroke-width="1" stroke-linejoin="round"/>
<!-- facial details -->
<circle cx="22" cy="18.5" r="2.2" fill="#071A24" stroke="#80FFDB" stroke-width="0.6"/>
<circle cx="21.3" cy="17.8" r="0.8" fill="#80FFDB"/>
<circle cx="13.5" cy="22.5" r="1.4" fill="#80FFDB"/>
<path d="M 11 26.5 Q 17 27 22 24.5" fill="none" stroke="#E76F51" stroke-width="1.8" stroke-linecap="round"/>
<!-- neck muscle & mane highlights -->
<path d="M 26 29 Q 31 36 28 46" fill="none" stroke="#80FFDB" stroke-width="1.5" stroke-linecap="round"/>
<path d="M 23 15 C 26 17, 30 20, 27 26" fill="none" stroke="#80FFDB" stroke-width="1.2" stroke-linecap="round" stroke-opacity="0.5"/>
''')


# ═══════════════════════════════════════════════════════════════════════════
# PAWN — Nautical Pearl-Crested Guardian
# ═══════════════════════════════════════════════════════════════════════════

_PAWN_W = _w_svg('''
<!-- drop shadow -->
<path d="M 18 56 C 18 58 24 60 32 60 C 40 60 46 58 46 56 L 46 52 C 46 50 40 48 32 48 C 24 48 18 50 18 52 Z" fill="#000000" fill-opacity="0.18" transform="translate(1, 1.5)"/>
<!-- wave-rimmed base -->
<path d="M 16 56 C 16 58 22 59 32 59 C 42 59 48 58 48 56 L 48 52 C 48 50 42 49 32 49 C 22 49 16 50 16 52 Z" fill="url(#wBase)" stroke="#4A3B2C" stroke-width="1.1"/>
<path d="M 18 53 Q 22 50 26 53 Q 30 50 34 53 Q 38 50 42 53 Q 46 50 46 52" fill="none" stroke="#D4AF37" stroke-width="0.6" stroke-opacity="0.6"/>
<!-- sleek contoured column -->
<path d="M 26 49 C 26 44 24 40 24 36 C 24 34 26 32 28 31 L 36 31 C 38 32 40 34 40 36 C 40 40 38 44 38 49 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="1"/>
<!-- scalloped clam-shell cradle -->
<path d="M 22 31 C 22 27 26 24 32 24 C 38 24 42 27 42 31 Z" fill="url(#wBody)" stroke="#4A3B2C" stroke-width="0.9"/>
<path d="M 24 30 Q 27 27 32 30 Q 37 27 40 30" fill="none" stroke="#D4AF37" stroke-width="0.6" stroke-opacity="0.55"/>
<!-- luminous spherical pearl -->
<circle cx="32" cy="17" r="7" fill="url(#wPearl)" stroke="#4A3B2C" stroke-width="1.1"/>
<!-- pearl specular highlight -->
<ellipse cx="29.5" cy="14.5" rx="3" ry="2.2" fill="#FFFFFF" fill-opacity="0.55"/>
<!-- pearl secondary glow -->
<ellipse cx="34" cy="19" rx="2" ry="1.5" fill="#FFFDF9" fill-opacity="0.25"/>
<!-- gold accent ring around pearl -->
<circle cx="32" cy="17" r="7.8" fill="none" stroke="#D4AF37" stroke-width="0.6" stroke-opacity="0.5"/>
<!-- inner rim -->
<path d="M 26 49 C 26 44 24 40 24 36" fill="none" stroke="#FFFDF9" stroke-width="0.4" stroke-opacity="0.4"/>
''')

_PAWN_B = _b_svg('''
<!-- drop shadow -->
<path d="M 18 56 C 18 58 24 60 32 60 C 40 60 46 58 46 56 L 46 52 C 46 50 40 48 32 48 C 24 48 18 50 18 52 Z" fill="#000000" fill-opacity="0.25" transform="translate(1.5, 2)"/>
<!-- wave-rimmed base -->
<path d="M 16 56 C 16 58 22 59 32 59 C 42 59 48 58 48 56 L 48 52 C 48 50 42 49 32 49 C 22 49 16 50 16 52 Z" fill="url(#bBase)" stroke="#2A9D8F" stroke-width="1.1"/>
<path d="M 18 53 Q 22 50 26 53 Q 30 50 34 53 Q 38 50 42 53 Q 46 50 46 52" fill="none" stroke="#F4A261" stroke-width="0.6" stroke-opacity="0.55"/>
<!-- column -->
<path d="M 26 49 C 26 44 24 40 24 36 C 24 34 26 32 28 31 L 36 31 C 38 32 40 34 40 36 C 40 40 38 44 38 49 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="1"/>
<!-- cradle -->
<path d="M 22 31 C 22 27 26 24 32 24 C 38 24 42 27 42 31 Z" fill="url(#bBody)" stroke="#2A9D8F" stroke-width="0.9"/>
<path d="M 24 30 Q 27 27 32 30 Q 37 27 40 30" fill="none" stroke="#F4A261" stroke-width="0.6" stroke-opacity="0.5"/>
<!-- bioluminescent pearl -->
<circle cx="32" cy="17" r="7" fill="url(#bPearl)" stroke="#2A9D8F" stroke-width="1.1"/>
<!-- pearl glow -->
<ellipse cx="29.5" cy="14.5" rx="3" ry="2.2" fill="#80FFDB" fill-opacity="0.45"/>
<ellipse cx="34" cy="19" rx="2" ry="1.5" fill="#4DD8B0" fill-opacity="0.2"/>
<!-- coral accent ring -->
<circle cx="32" cy="17" r="7.8" fill="none" stroke="#E76F51" stroke-width="0.6" stroke-opacity="0.45"/>
<!-- rim -->
<path d="M 26 49 C 26 44 24 40 24 36" fill="none" stroke="#80FFDB" stroke-width="0.4" stroke-opacity="0.35"/>
''')


# ═══════════════════════════════════════════════════════════════════════════
# Assemble the mapping
# ═══════════════════════════════════════════════════════════════════════════

PIECE_SVGS: dict[tuple[bool, int], str] = {
    (chess.WHITE, chess.KING):   _KING_W,
    (chess.BLACK, chess.KING):   _KING_B,
    (chess.WHITE, chess.QUEEN):  _QUEEN_W,
    (chess.BLACK, chess.QUEEN):  _QUEEN_B,
    (chess.WHITE, chess.ROOK):   _ROOK_W,
    (chess.BLACK, chess.ROOK):   _ROOK_B,
    (chess.WHITE, chess.BISHOP): _BISHOP_W,
    (chess.BLACK, chess.BISHOP): _BISHOP_B,
    (chess.WHITE, chess.KNIGHT): _KNIGHT_W,
    (chess.BLACK, chess.KNIGHT): _KNIGHT_B,
    (chess.WHITE, chess.PAWN):   _PAWN_W,
    (chess.BLACK, chess.PAWN):   _PAWN_B,
}


# ---------------------------------------------------------------------------
# 2. QSS Stylesheet
# ---------------------------------------------------------------------------
STYLESHEET = """
/* ===== Aqua Chess – Beach & Ocean Resort Theme ===== */

/* --- Main window --- */
QMainWindow {
    background: transparent;
}

/* --- Central area (painted by CentralBackground) --- */
QWidget#centralArea {
    background: transparent;
}

/* --- Sidebar: Frosted Sea-Glass --- */
QWidget#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0 rgba(12, 48, 66, 0.74),
        stop: 1 rgba(8, 30, 44, 0.78));
    border: 1.5px solid rgba(145, 235, 248, 0.36);
    border-radius: 16px;
}

/* --- Glassmorphism Group Boxes (cards) --- */
QGroupBox {
    background: rgba(10, 38, 54, 0.55);
    border: 1px solid rgba(128, 255, 219, 0.28);
    border-radius: 12px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #80FFDB;
    font-size: 12px;
}

/* --- Labels --- */
QLabel {
    color: #FFFFFF;
    font-size: 13px;
    background: transparent;
}
QLabel#titleLabel {
    font-size: 22px;
    font-weight: bold;
    color: #FFFDF9;
    letter-spacing: 1px;
    padding-bottom: 2px;
}
QLabel#subtitleLabel {
    font-size: 12px;
    color: #80FFDB;
}
QLabel#statusLabel {
    font-size: 12px;
    font-weight: bold;
    color: #E0F2F1;
    background: rgba(7, 26, 36, 0.75);
    border: 1px solid rgba(128, 255, 219, 0.30);
    border-radius: 8px;
    padding: 8px 10px;
    min-height: 22px;
}
QLabel#bannerStatusLabel {
    font-size: 17pt;
    font-weight: bold;
    color: #FFFDF9;
    background: transparent;
    border: none;
    padding: 0;
}

/* --- Post-Game Inspect Controls (inside TurnIndicatorBanner) --- */
QFrame#inspectDivider {
    background-color: rgba(128, 255, 219, 0.28);
    border: none;
}
QPushButton#inspectResultsBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 rgba(42, 157, 143, 0.45),
        stop: 1.00 rgba(19, 80, 91, 0.72));
    color: #A7F3D0;
    border: 1.5px solid rgba(128, 255, 219, 0.55);
    border-radius: 10px;
    padding: 6px 14px;
    min-height: 18px;
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
    font-weight: 700;
}
QPushButton#inspectResultsBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 rgba(56, 189, 173, 0.65),
        stop: 1.00 rgba(29, 120, 116, 0.88));
    border: 1.5px solid #80FFDB;
    color: #FFFFFF;
}
QPushButton#inspectResultsBtn:pressed {
    background: rgba(13, 62, 70, 0.92);
    border: 1.5px solid rgba(128, 255, 219, 0.45);
    padding: 7px 14px 5px 14px;
}
QPushButton#inspectNewGameBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 #FFB199,
        stop: 0.14 #FF8E72,
        stop: 0.54 #EC6A4E,
        stop: 0.94 #C94931,
        stop: 1.00 #DF6853);
    color: #FFFFFF;
    border: 1.5px solid rgba(255, 255, 255, 0.55);
    border-radius: 10px;
    padding: 6px 14px;
    min-height: 18px;
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
    font-weight: 700;
}
QPushButton#inspectNewGameBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 #FFC2AE,
        stop: 0.14 #FFA087,
        stop: 0.54 #F4765A,
        stop: 0.94 #D3533B,
        stop: 1.00 #EB7A63);
    border: 1.5px solid rgba(255, 255, 255, 0.92);
}
QPushButton#inspectNewGameBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 #B83E28,
        stop: 0.25 #C2452E,
        stop: 0.75 #D15037,
        stop: 1.00 #D9583E);
    border: 1.5px solid rgba(255, 255, 255, 0.45);
    padding: 7px 14px 5px 14px;
}
QLabel#sectionLabel {
    font-size: 11px;
    font-weight: bold;
    color: #80FFDB;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 4px;
}
QLabel#capturedLabel {
    background: rgba(7, 26, 36, 0.60);
    border: 1px solid rgba(128, 255, 219, 0.18);
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 13px;
    color: #E0F7FA;
    min-height: 20px;
}

/* --- Buttons (Coral-Sunset Aqua-Glass) --- */
QPushButton {
    background-color: #E76F51;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: bold;
    min-height: 22px;
}
QPushButton:hover {
    background-color: #D4573D;
}
QPushButton:pressed {
    background-color: #C04B33;
}
QPushButton:disabled {
    background-color: rgba(231, 111, 81, 0.40);
    color: rgba(255, 255, 255, 0.50);
}
QPushButton#actionBtn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 #FFB199,
        stop: 0.12 #FF8E72,
        stop: 0.52 #EC6A4E,
        stop: 0.92 #C94931,
        stop: 1.00 #DF6853);
    color: #FFFFFF;
    border: 1.5px solid rgba(255, 255, 255, 0.55);
    border-radius: 13px;
    padding: 0px 10px;
    min-height: 48px;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.3px;
}
QPushButton#actionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 #FFC2AE,
        stop: 0.14 #FFA087,
        stop: 0.54 #F4765A,
        stop: 0.92 #D3533B,
        stop: 1.00 #EB7A63);
    border: 1.5px solid rgba(255, 255, 255, 0.90);
}
QPushButton#actionBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 #B83E28,
        stop: 0.20 #C2452E,
        stop: 0.72 #D15037,
        stop: 1.00 #D9583E);
    border: 1.5px solid rgba(255, 255, 255, 0.45);
    padding: 2px 10px 0px 10px;
    min-height: 46px;
}
QPushButton#actionBtn:disabled {
    background: rgba(180, 110, 98, 0.38);
    border: 1.5px solid rgba(255, 255, 255, 0.22);
    color: rgba(255, 255, 255, 0.45);
    padding: 0px 10px;
    min-height: 48px;
}

/* --- Sound Controls (Coastal Sea-Glass Bar) --- */
QFrame#soundPanel {
    background-color: rgba(7, 26, 36, 0.62);
    border: 1px solid rgba(128, 255, 219, 0.24);
    border-radius: 9px;
}
QPushButton#muteBtn {
    background-color: rgba(42, 157, 143, 0.30);
    color: #FFFDF9;
    border: 1px solid rgba(128, 255, 219, 0.40);
    border-radius: 6px;
    padding: 0px;
    min-height: 24px;
    font-size: 13px;
}
QPushButton#muteBtn:hover {
    background-color: rgba(42, 157, 143, 0.52);
    border-color: #80FFDB;
}
QPushButton#muteBtn:pressed {
    background-color: rgba(29, 120, 116, 0.70);
}
QPushButton#muteBtn:checked {
    background-color: rgba(231, 111, 81, 0.25);
    color: #F4A261;
    border: 1px solid rgba(231, 111, 81, 0.60);
}
QPushButton#muteBtn:checked:hover {
    background-color: rgba(231, 111, 81, 0.40);
    border-color: #E76F51;
}
QSlider#volumeSlider {
    background: transparent;
    min-height: 20px;
}
QSlider#volumeSlider::groove:horizontal {
    height: 6px;
    background: rgba(7, 26, 36, 0.85);
    border: 1px solid rgba(128, 255, 219, 0.22);
    border-radius: 3px;
}
QSlider#volumeSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2A9D8F, stop:1 #80FFDB);
    border: 1px solid rgba(128, 255, 219, 0.35);
    border-radius: 3px;
}
QSlider#volumeSlider::add-page:horizontal {
    background: rgba(7, 26, 36, 0.85);
    border: 1px solid rgba(128, 255, 219, 0.18);
    border-radius: 3px;
}
QSlider#volumeSlider::handle:horizontal {
    background: #FFFDF9;
    border: 2px solid #E76F51;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider#volumeSlider::handle:horizontal:hover {
    background: #F4A261;
    border-color: #FFFDF9;
}
QLabel#volumeValueLabel {
    color: #E0F2F1;
    font-size: 11px;
    font-weight: bold;
    background: transparent;
}

/* --- Combo Boxes (Aqua-Glass Dropdowns) --- */
QComboBox {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 rgba(48, 148, 168, 0.55),
        stop: 0.18 rgba(18, 68, 84, 0.78),
        stop: 0.85 rgba(12, 48, 62, 0.85),
        stop: 1.00 rgba(42, 135, 155, 0.50));
    color: #FFFFFF;
    border: 1.5px solid rgba(145, 235, 248, 0.60);
    border-radius: 12px;
    padding: 0px 14px;
    min-height: 44px;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
    font-weight: 600;
}
QComboBox:hover,
QComboBox:on {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 rgba(72, 182, 204, 0.66),
        stop: 0.18 rgba(22, 82, 102, 0.82),
        stop: 0.85 rgba(14, 56, 72, 0.88),
        stop: 1.00 rgba(54, 156, 178, 0.58));
    border: 1.5px solid rgba(145, 235, 248, 0.92);
}
QComboBox:disabled {
    background: rgba(14, 52, 66, 0.48);
    border: 1.5px solid rgba(145, 235, 248, 0.24);
    color: rgba(255, 255, 255, 0.45);
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 34px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 rgba(145, 235, 248, 0.14),
        stop: 1.00 rgba(145, 235, 248, 0.04));
    border-left: 1px solid rgba(145, 235, 248, 0.28);
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
}
QComboBox::drop-down:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop: 0.00 rgba(145, 235, 248, 0.24),
        stop: 1.00 rgba(72, 202, 228, 0.10));
}
QComboBox::down-arrow {
    image: none;
    width: 0px;
    height: 0px;
}
QFrame#aquaComboPopup {
    background: transparent;
    border: none;
}
QComboBox QAbstractItemView {
    background-color: rgba(9, 40, 54, 0.96);
    color: #FFFFFF;
    border: 1.5px solid rgba(145, 235, 248, 0.55);
    border-radius: 10px;
    padding: 5px;
    selection-background-color: rgba(72, 202, 228, 0.35);
    selection-color: #FFFFFF;
    outline: none;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
    font-weight: 500;
}
QComboBox QAbstractItemView::item {
    min-height: 32px;
    padding: 4px 10px;
    border-radius: 7px;
}
QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {
    background-color: rgba(72, 202, 228, 0.35);
    color: #FFFFFF;
}

/* --- Table Widget (Move History) --- */
QTableWidget {
    background-color: rgba(7, 26, 36, 0.65);
    color: #FFFFFF;
    border: 1px solid rgba(128, 255, 219, 0.15);
    border-radius: 8px;
    gridline-color: rgba(128, 255, 219, 0.08);
    font-size: 12px;
    selection-background-color: rgba(231, 111, 81, 0.45);
    selection-color: #FFFFFF;
    outline: none;
}
QTableWidget::item {
    padding: 4px 6px;
}
QTableWidget::item:selected {
    background-color: rgba(231, 111, 81, 0.45);
}

QHeaderView {
    background: transparent;
}
QHeaderView::section {
    background-color: rgba(7, 26, 36, 0.80);
    color: #80FFDB;
    border: none;
    border-bottom: 1px solid rgba(128, 255, 219, 0.15);
    padding: 5px 8px;
    font-size: 11px;
    font-weight: bold;
}

/* --- Scrollbar (Thin, Coral Accent) --- */
QScrollBar:vertical {
    background: rgba(7, 26, 36, 0.30);
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #E76F51;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #D4573D;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
    border: none;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background: rgba(7, 26, 36, 0.30);
    height: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #E76F51;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #D4573D;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
    background: none;
    border: none;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

/* --- Tooltips --- */
QToolTip {
    background-color: rgba(7, 26, 36, 0.92);
    color: #FFFFFF;
    border: 1px solid #E76F51;
    border-radius: 4px;
    padding: 4px;
    font-size: 11px;
}
"""


# ---------------------------------------------------------------------------
# 3. Color Constants
# ---------------------------------------------------------------------------
COLORS: dict[str, str] = {
    'light_square':  '#FAF0CA',                 # Warm sunlit sand
    'light_square2': '#EAD2AC',                 # Sand shadow
    'dark_square':   '#1D7874',                 # Tropical lagoon
    'dark_square2':  '#13505B',                 # Deep lagoon
    'board_border':  '#5C3D2E',                 # Rich driftwood teak
    'border_inner':  '#D4AF37',                 # Brass/gold trim
    'last_move':     'rgba(244, 162, 97, 0.45)',  # Sunset coral-amber
    'legal_move':    '#80FFDB',                 # Bioluminescent cyan
    'check':         '#E63946',                 # Red coral
    'selected':      '#D4AF37',                 # Golden aqua selection
    'coord_text':    '#D4AF37',                 # Nautical gold
    'bg_deep_ocean': '#004E64',
    'bg_turquoise':  '#00A5CF',
    'bg_shallow':    '#48CAE4',
    'bg_sand':       '#F6E2B3',
    'bg_sand_dark':  '#E6C786',
    'sidebar_bg':    'rgba(10,38,54,0.68)',
    'eval_white':    '#FFF8E7',
    'eval_black':    '#071A24',
    'coral_accent':  '#E76F51',
    'seafoam_white': 'rgba(255, 255, 255, 0.55)',
    'caustic_light': 'rgba(72, 202, 228, 0.12)',
}
