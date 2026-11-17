"""Two synthetic 'before/after' frames for tokn vision track (no real data)."""
from PIL import Image, ImageDraw
W, H = 800, 500
def frame(blue_x, add_square):
    im = Image.new("RGB", (W, H), (238, 240, 235)); d = ImageDraw.Draw(im)
    d.ellipse([120, 180, 220, 280], fill=(200, 60, 50))           # red disc: stays put
    d.ellipse([blue_x, 200, blue_x + 90, 290], fill=(40, 90, 200)) # blue disc: moves right
    if add_square:
        d.rectangle([600, 60, 700, 160], fill=(40, 150, 70))       # green square: appears
    return im
frame(320, False).save("before.png")
frame(470, True).save("after.png")
