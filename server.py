from flask import Flask, Response, send_file, request
import threading
import struct
import time
import io
import yaml


with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

server_host = config["server"]["host"]
server_port = config["server"]["port"]
pipe_image_path = config["pipe"]["image"]["path"]
pipe_tire_settings_path = config["pipe"]["tire-settings"]["path"]
import os

app = Flask(__name__)

latest_image = None
lock = threading.Lock()
clients = []


def read_pipe_bytes(pipe, size):
    buf = b""
    while len(buf) < size:
        chunk = pipe.read(size - len(buf))
        if not chunk:
            return None # end of a file (incorrect length)
        buf += chunk
    return buf


def read_image_pipe():
    global latest_image
    while True:
        try:
            if not os.path.exists(pipe_image_path):
                time.sleep(0.5)
                continue
            with open(pipe_image_path, "rb") as pipe:
                while True:
                    size_bytes = read_pipe_bytes(pipe, 4)
                    if size_bytes is None:
                        break
                    size = struct.unpack(">I", size_bytes)[0]

                    data = read_pipe_bytes(pipe, size)
                    if data is None:
                        break

                    with lock:
                        latest_image = data
                    print(f"Image received: {size} bytes")
        except Exception as e:
            print(f"Error while reading image pipe: {e}")
        time.sleep(0.5) # wait before next read


def event_stream():
    last_sent = None
    while True:
        time.sleep(0.5) # update frequency
        with lock:
            current = latest_image
        if current is not None and current != last_sent:
            last_sent = current
            yield f"data: new image available\n\n"


@app.route("/image")
def image():
    with lock:
        if latest_image is None:
            return "", 404
        return send_file(
            path_or_file=io.BytesIO(latest_image),
            mimetype="image/png",
            as_attachment=False,
            download_name="image.png",
        )


@app.route("/update")
def update():
    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/tire-settings", methods=["POST"])
def tire_settings():
    try:
        if not os.path.exists(pipe_tire_settings_path):
            return "Pipe doesn't exists", 500

        data = request.get_data(as_text=True)
        if len(data) > 200:
            return "Request too long (max 200 characters)", 400

        with open(pipe_tire_settings_path, "w") as pipe:
            pipe.write(data)
        return "ok", 200

    except Exception as e:
        print(f"Error in tire-settings: {e}")
        return "Internal server error", 500


if __name__ == "__main__":
    threading.Thread(target=read_image_pipe, daemon=True).start()
    app.run(host=server_host, port=server_port, threaded=True)
