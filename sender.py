import os
import time
import random

FIFO = "image_pipe"
IMAGE_FOLDER = "images"

def send_images():
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

if __name__ == "__main__":
    send_images()
