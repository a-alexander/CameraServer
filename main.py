from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import imutils
import time
import cv2

vs = VideoStream(src=0, resolution=(720, 480)).start()
time.sleep(2.0)

outputFrame = None
lock = threading.Lock()
# initialize a flask object
app = Flask(__name__)


def detect_motion():
    print('Starting camera feed thread...')
    global outputFrame
    while True:
        # read the next frame from the video stream, resize it,
        # convert the frame to grayscale, and blur it
        frame = vs.read()
        frame = imutils.resize(frame, width=800)
        with lock:
            outputFrame = frame.copy()


def generate():
    print('Generating next frame...')
    # grab global references to the output frame and lock variables
    global outputFrame, lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
               bytearray(encodedImage) + b'\r\n')


@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':
    t = threading.Thread(target=detect_motion)
    t.daemon = True
    t.start()
    # start the flask app
    app.run(port=9999, debug=True,
            threaded=True, use_reloader=False)
# release the video stream pointer
vs.stop()
