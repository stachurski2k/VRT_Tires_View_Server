import os
import time
import random

# image sender for server.py testing

FIFO = "image_pipe"
IMAGE_FOLDER = "images"


def ensure_fifo(path):
    if not os.path.exists(path):
        try:
            os.mkfifo(path)
            print(f"Pipe created: {path}")
        except FileExistsError:
            pass


def send_images():
    ensure_fifo(FIFO)
    while True:
        try:
            with open(FIFO, "wb") as pipe:
                while True:
                    for filename in sorted(os.listdir(IMAGE_FOLDER)):
                        if filename.endswith(".png"):
                            path = os.path.join(IMAGE_FOLDER, filename)
                            with open(path, "rb") as img:
                                data = img.read()
                                size = len(data).to_bytes(4, byteorder="big")
                                pipe.write(size + data)
                                pipe.flush()
                                time.sleep(random.randint(1, 5))
        except Exception as e:
            print(e)
            time.sleep(1)


if __name__ == "__main__":
    send_images()
