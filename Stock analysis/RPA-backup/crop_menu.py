# -*- coding: utf-8 -*-
from PIL import Image

# Open the screenshot
img = Image.open(r"E:\G-AI-1\Stock analysis\RPA_Automation\right_click_menu.png")

# Crop the menu area
# Menu starts at x=500, y=190 (approx) and ends around x=650, y=510
menu_crop = img.crop((500, 180, 650, 520))
menu_crop.save(r"E:\G-AI-1\Stock analysis\RPA_Automation\menu_cropped.png")

print("Cropped menu saved. Width:", menu_crop.width, "Height:", menu_crop.height)
