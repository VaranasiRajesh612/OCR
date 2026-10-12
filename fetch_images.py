
import csv
import re
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, UnidentifiedImageError

# Authorized test-image endpoint
IMAGE_URL = "https://login.gitam.edu/CaptchaImage.ashx?c=_khJx-YQOGMCdD7St2euAg2"

OUTPUT_DIR = Path("image_dataset")
IMAGE_DIR = OUTPUT_DIR / "raw_images"
MANIFEST = OUTPUT_DIR / "manifest.csv"

INTERVAL_SECONDS = 5
MAX_ATTEMPTS = 100
TIMEOUT_SECONDS = 20
MAX_IMAGE_BYTES = 10 * 1024 * 1024

SUPPORTED_FORMATS = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WEBP": ".webp",
    "GIF": ".gif",
    "BMP": ".bmp",
}


def get_next_serial_number():
    """Continue numbering from the highest existing image number."""
    pattern = re.compile(r"^image_(\d+)\.[^.]+$", re.IGNORECASE)
    highest = 0

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    for path in IMAGE_DIR.iterdir():
        match = pattern.match(path.name)
        if match and path.is_file():
            highest = max(highest, int(match.group(1)))

    return highest + 1


def load_existing_records():
    if not MANIFEST.exists():
        return []

    with MANIFEST.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def save_manifest(records):
    with MANIFEST.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["filename", "label", "status"],
        )
        writer.writeheader()
        writer.writerows(records)


def fetch_image(session, serial_number):
    try:
        response = session.get(
            IMAGE_URL,
            timeout=TIMEOUT_SECONDS,
            headers={"Cache-Control": "no-cache"},
        )
        response.raise_for_status()

        content_type = (
            response.headers.get("Content-Type", "")
            .split(";")[0]
            .strip()
            .lower()
        )

        if not content_type.startswith("image/"):
            print("Response is not an image; skipped.")
            return None

        data = response.content

        if not data or len(data) > MAX_IMAGE_BYTES:
            print("Image is empty or exceeds the size limit.")
            return None

        with Image.open(BytesIO(data)) as image:
            image.verify()
            image_format = image.format

        extension = SUPPORTED_FORMATS.get(image_format)

        if not extension:
            print("Unsupported image format; skipped.")
            return None

        filename = f"image_{serial_number:05d}{extension}"
        destination = IMAGE_DIR / filename

        # Never overwrite an existing image.
        if destination.exists():
            print(f"File already exists; skipped: {filename}")
            return None

        destination.write_bytes(data)

        print(f"Saved: {destination}")

        return {
            "filename": filename,
            "label": "",
            "status": "downloaded",
        }

    except (
        requests.RequestException,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:
        print(f"Download failed: {error}")
        return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        attempts = int(
            input(f"Maximum attempts [{MAX_ATTEMPTS}]: ")
            or MAX_ATTEMPTS
        )
        interval = float(
            input(f"Interval in seconds [{INTERVAL_SECONDS}]: ")
            or INTERVAL_SECONDS
        )

        if attempts < 1 or interval < 0:
            raise ValueError

    except ValueError:
        print("Enter a positive attempt count and non-negative interval.")
        return

    records = load_existing_records()

    # Resume numbering from the files already present.
    serial_number = get_next_serial_number()

    print(f"Starting from image number: {serial_number}")
    print(f"Maximum attempts: {attempts}")

    with requests.Session() as session:
        for attempt in range(1, attempts + 1):
            print(f"\nAttempt {attempt}/{attempts}")

            record = fetch_image(session, serial_number)

            if record:
                records.append(record)
                save_manifest(records)
                serial_number += 1

            if attempt < attempts:
                time.sleep(interval)

    print("\nCollection finished.")
    print(f"Images saved in: {IMAGE_DIR.resolve()}")
    print(f"Manifest saved at: {MANIFEST.resolve()}")
    print(f"Next image number: {serial_number}")


if __name__ == "__main__":
    main()
