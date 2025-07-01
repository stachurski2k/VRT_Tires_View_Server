from flask import Flask, Response, send_file
import threading
import struct
import time
import io

app = Flask(__name__)

FIFO = "image_pipe"
latest_image = None
lock = threading.Lock()

clients = []


def read_exact(pipe, size):
    buf = b""
    while len(buf) < size:
        chunk = pipe.read(size - len(buf))
        if not chunk:
            # koniec danych (EOF) — zwróć None, by sygnalizować zakończenie czytania
            return None
        buf += chunk
    return buf


def read_pipe():
    global latest_image
    while True:
        try:
            with open(FIFO, "rb") as pipe:
                while True:
                    size_bytes = read_exact(pipe, 4)
                    if size_bytes is None:
                        # EOF - piszący zamknął FIFO, przejdź do ponownego otwarcia
                        break
                    size = struct.unpack(">I", size_bytes)[0]

                    data = read_exact(pipe, size)
                    if data is None:
                        # EOF - przerwij czytanie i ponownie otwórz FIFO
                        break

                    with lock:
                        latest_image = data
                    print(f"Odebrano obrazek: {size} bajtów")
        except Exception as e:
            print(f"Błąd przy czytaniu z rury: {e}")

        # krótka przerwa zanim spróbujemy otworzyć FIFO ponownie
        time.sleep(0.5)


def event_stream():
    """Generator do SSE, który wysyła event, gdy pojawi się nowe zdjęcie."""
    last_sent = None
    while True:
        time.sleep(0.5)
        with lock:
            current = latest_image
        if current is not None and current != last_sent:
            last_sent = current
            yield f"data: nowy_obrazek\n\n"


@app.route("/image")
def image():
    with lock:
        if latest_image is None:
            return "Brak obrazka", 404
        return send_file(
            io.BytesIO(latest_image),
            mimetype="image/png",
            as_attachment=False,
            download_name="image.png",
        )


@app.route("/update")
def update():
    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    threading.Thread(target=read_pipe, daemon=True).start()
    # app.run(host="0.0.0.0", port=2323, threaded=True, ssl_context=('cert.pem', 'key.pem'))
    app.run(host="0.0.0.0", port=8080, threaded=True)
