# Placeholder palette. A light nod to the neo-noir corporate direction from the
# spec (dark navy + cyan glow); the final visual system lands in the art pass.
BACKGROUND = (12, 14, 22)
TEXT = (226, 232, 240)
BUTTON_IDLE = (26, 30, 44)
BUTTON_HOVER = (38, 44, 64)
BUTTON_FOCUS_BORDER = (58, 214, 255)
BUTTON_TEXT = (226, 232, 240)
BUTTON_DISABLED = (18, 20, 28)
BUTTON_TEXT_DISABLED = (74, 80, 94)
PANEL_BACKGROUND = (18, 21, 32)
SEGMENT_SECONDARY = (255, 158, 68)
"""A second, warm accent for a two-series chart (e.g. two segments/
processes overlaid on one histogram) - distinct from BUTTON_FOCUS_BORDER's
own cyan. Reuses PRODUCT_MANAGER's own established avatar_color
(narrative/npc.py) rather than inventing a new hue, since it's already a
validated, visually distinct tone in this palette."""
