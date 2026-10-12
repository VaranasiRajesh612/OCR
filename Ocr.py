
import cv2
import numpy as np
import matplotlib.pyplot as plt

image_path = "C:/CAPTCHA/image_dataset/raw_images/image_00001.png"

img = cv2.imread(image_path)
if img is None:
    raise FileNotFoundError(image_path)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Enlarge small text before processing
gray = cv2.resize(
    gray, None, fx=4, fy=4,
    interpolation=cv2.INTER_CUBIC
)

# Improve local contrast
clahe = cv2.createCLAHE(
    clipLimit=2.0, tileGridSize=(8, 8)
)
enhanced = clahe.apply(gray)

# Local thresholding
adaptive = cv2.adaptiveThreshold(
    enhanced, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    21, 5
)

# Global thresholding for comparison
_, otsu = cv2.threshold(
    enhanced, 0, 255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)

# Display the different results
images = {
    "Original grayscale": gray,
    "CLAHE enhanced": enhanced,
    "Adaptive threshold": adaptive,
    "Otsu threshold": otsu,
}

fig, axes = plt.subplots(2, 2, figsize=(12, 6))
for ax, (name, result) in zip(axes.flat, images.items()):
    ax.imshow(result, cmap="gray")
    ax.set_title(name)
    ax.axis("off")

plt.tight_layout()
plt.show()
