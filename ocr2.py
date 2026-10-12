import cv2

img = cv2.imread("C:/CAPTCHA/image_dataset/raw_images/image_00001.png", cv2.IMREAD_GRAYSCALE)

# Keep pixels darker than the chosen threshold
threshold = 100

result = cv2.threshold(
    img, threshold, 255, cv2.THRESH_BINARY_INV
)[1]

cv2.imwrite("dark_pixels.png", result)