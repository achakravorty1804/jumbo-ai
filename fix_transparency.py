"""One-off fix: make near-white pixels in jumbo_sidebar.png fully
transparent, including enclosed pockets (like between the legs) that
the original background-removal tool missed. Run once, then delete
this file."""

from PIL import Image

SRC = "static/jumbo/jumbo_sidebar.png"
BACKUP = "static/jumbo/jumbo_sidebar_backup.png"

img = Image.open(SRC).convert("RGBA")
img.save(BACKUP)  # keep the original just in case

pixels = img.getdata()
new_pixels = []

WHITE_THRESHOLD = 235  # pixels with R, G and B all above this become transparent

for r, g, b, a in pixels:
    if r >= WHITE_THRESHOLD and g >= WHITE_THRESHOLD and b >= WHITE_THRESHOLD:
        new_pixels.append((r, g, b, 0))
    else:
        new_pixels.append((r, g, b, a))

img.putdata(new_pixels)
img.save(SRC)

print("Done. Backup saved at", BACKUP)