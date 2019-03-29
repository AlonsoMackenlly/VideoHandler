import datetime

import os
import threading
from threading import Thread
import json
import io
import time
import cv2
from PIL import Image

import tornado.ioloop, tornado.web, tornado.gen, tornado.escape
# from control_pane.models import Stream
from termcolor import colored

LOGGING = True
PORT = 15152

streams = {}

no_image = Image.open("/root/django/control_pane/static/img/noimage.jpg")
#http://localhost:15152/image?title=drone3-1

def handleFrame(title):
    streams[title, "stop_trigger"] = False
    streams[title, "telemetry_required"] = False
    streams[title, "nn_required"] = False
    stream_path = streams[title, "stream_path"]
    vs = cv2.VideoCapture(stream_path)
    while True:
        if streams[title, "stop_trigger"] == True:
            break
        ret, frame = vs.read()
        if ret:
            # frame = cv2.imread('/root/django/control_pane/lib/VideoHandler/living_room.jpg', cv2.IMREAD_UNCHANGED)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if streams[title, "telemetry_required"] == True:
                draw_text_on_cv_frame(frame, "Altutide: 10 m.", (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6, [255, 255, 255], 2)
                draw_text_on_cv_frame(frame, "Speed: 5 m/s", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, [255, 255, 255], 2)
            streams[title, "img"] = frame

def draw_text_on_cv_frame(frame, text, position, font, font_size, color, line_size):
    cv2.putText(frame, text, position, font, font_size, [0, 0, 0], line_size + 5)
    # cv2.putText(frame, text, position, font, font_size, color, line_size)
    return frame

def write_header(tornadoself):
    tornadoself.set_header("Access-Control-Allow-Origin", "*")
    tornadoself.set_header("Access-Control-Allow-Headers", "*")
    tornadoself.set_header("Access-Control-Allow-Methods", "*")
    tornadoself.set_header("Access-Control-Allow-Credentials", "true")

    tornadoself.set_header("Cache-Control",
                           "no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0")
    tornadoself.set_header("Connection", "close")
    tornadoself.set_header("Content-Type", "multipart/x-mixed-replace;boundary=--boundarydonotcross")
    tornadoself.set_header("Expires", "Mon, 3 Jan 2000 12:34:56 GMT")
    tornadoself.set_header("Pragma", "no-cache")


def write_image(tornadoself, params):
    o = io.BytesIO()

    try:
        img = Image.fromarray(streams[params["title"], "img"])
    except TypeError:
        img = streams[params["title"], "img"]

    img.save(o, format="JPEG")
    s = o.getvalue()

    tornadoself.write("--boundarydonotcross\n")
    tornadoself.write("Content-type: image/jpeg\r\n")
    tornadoself.write("Content-length: %s\r\n\r\n" % len(s))
    tornadoself.write(s)


def write_status(tornadoself, message, status="info"):
    if status == "info":
        if message.find("success") != -1:
            status = "success"
        elif message.find("already") != -1:
            status = "warn"
        elif message.find("ERROR") != -1:
            status = "error"
        else:
            status = "info"
    tornadoself.write(json.dumps({"message": message, "status": status}))
    tornadoself.finish()


class APIHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        write_header(self)

        action = self.get_argument("action", None)
        title = self.get_argument("title", None)
        obj = self.get_argument("obj", None)

        if action == "start":
            write_status(self, start_thread(title))
        elif action == "stop":
            write_status(self, stop_thread(title))
        elif action == "restart":
            write_status(self, restart_thread(title))
        elif action == "start-all":
            write_status(self, start_threads())
        elif action == "stop-all":
            write_status(self, stop_threads())
        elif action == "restart-all":
            write_status(self, restart_threads())

        elif action == "create":
            json_parsed = json.loads(obj)
            ilog(str(json_parsed))
            new_stream = Stream.create(json_parsed['title'], json_parsed['stream_in'],json_parsed['nn_required'], json_parsed['width'],
                                       json_parsed['height'],
                                       json_parsed['fps'])
            new_stream.save()
            log("New stream successfully created. title - %s, stream_in - %s, nn_required - %s, width - %s, height - %s, fps - %s" % (
                json_parsed['title'], json_parsed['stream_in'],json_parsed['nn_required'], json_parsed['width'], json_parsed['height'],
                json_parsed['fps']),
                "green")
            init_thread(new_stream.title)
            write_status(self, "Stream successfully created")


        elif action == "delete":
            stream = Stream.objects.filter(title=title).last()
            if stream is not None:
                stream.delete()
                log("Stream successful deleted. title - %s" % title, "green")
            else:
                log("Stream with title %s does not exist" % title, "red")
        elif action == "update":
            log("param update", "cyan")

        elif action == "log":
            for thread in threading.enumerate():
                log(thread.name, "cyan")
        else:
            log("Unexpected action - %s" % action, "red")

    def options(self):
        self.set_status(204)
        self.finish()
 

class ImageHandler(tornado.web.RequestHandler):
    def get(self):
        # Переделать без get_params
        params = get_params(self.request.uri)
        write_header(self)
        while True:
            write_image(self, params)
            time.sleep(0.3)
        

    def options(self):
        # no body
        self.set_status(204)
        self.finish()


def get_params(uri):
    params = {}
    params_tmp = str(uri).split("/")[1].split("?")[1].split("&")

    for item in params_tmp:
        k = item.split("=")[0]
        v = item.split("=")[1]
        params[k] = v
    return params


def init_thread(title):
    log("Initializing thread %s" % title, "blue")
    # stream = Stream.objects.filter(title=title).last()
    # if stream != None:
    stream_path = "/dev/video0"
    # stream_path = stream.stream_input
    streams[title, 'img'] = no_image
    streams[title, "stream_path"] = stream_path
    streams[title, "stop_trigger"] = False
    streams[title, "telemetry_required"] = False
    streams[title, "nn_required"] = False
    Thread(target = handleFrame, args=(title,)).start()
    log("Thread %s successfully initialized" % title, "green")
    # else:
    #     log("Thread %s do not initialized" % title, "orange")

def init_threads():
    log("Initializing all threads", "blue")
    # streams_django = Stream.objects.all()
    # for stream in streams_django:
    #     streams[stream.title, "img"] = no_image
    #     streams[stream.title, "stop_trigger"] = False
    #     log("Thread %s successfully initialized" % stream.title, "green")
    # streams_django = Stream.objects.all()
    # for stream in streams_django:
    init_thread("drone3-1")


def start_thread(title):
    log("Starting thread %s" % title, "blue")
    flag_started = False
    for thread in threading.enumerate():
        if title == thread.name:
            flag_started = True
            break
    if not flag_started:
        streams[title, "img"] = no_image
        streams[title, "stop_trigger"] = False

        stream_object = Stream.objects.filter(title=title).last()

        # if stream_object.nn_required:
        # target = detect
        # else:
        #     target = retransmission

        # thread = Thread(target=target, args=(stream_object.stream_input, stream_object.title))
        # thread.start()
        # msg = "Thread %s is successfully started" % title
        # log(msg, "green")
        # time.sleep(0.2)  # DELAY
        # return msg
    else:
        msg = "Thread %s is already started" % title
        log(msg, "yellow")
        return msg


def start_threads():
    log("Starting all threads", "blue")
    streams_django = Stream.objects.all().order_by('title')

    flag_ok = True
    for stream in streams_django:
        flag_ok &= (start_thread(stream.title).find("successful") != -1 or start_thread(stream.title).find(
            "already") != -1)

    if flag_ok:
        msg = "Threads is successfully started"
        log(msg, "green")
        return msg
    else:
        msg = "ERROR"
        log(msg, "red")
        return msg


def stop_thread(title):
    log("Stopping thread %s" % title, "blue")
    if not streams[title, "stop_trigger"]:
        streams[title, "stop_trigger"] = True
        msg = "Thread %s is successfully stopped" % title
        log(msg, "green")
        return msg
    else:
        msg = "Thread %s is already stopped" % title
        log(msg, "yellow")
        return msg


def stop_threads():
    log("Stopping all threads", "blue")
    streams_django = Stream.objects.all()

    for stream in streams_django:
        stop_thread(stream.title)

    msg = "Threads is successfully stopped"
    log(msg, "green")
    return msg


def restart_thread(title):
    log("Restarting thread %s" % title, "blue")

    stop_thread(title)
    restarted_thread = find_thread(title)
    if restarted_thread is not None:
        while restarted_thread.is_alive():
            time.sleep(0.1)  # DO NOTHING

    if start_thread(title).find("successful") != -1:
        msg = "Thread %s is successfully restarted" % title
        log(msg, "green")
        return msg
    else:
        msg = "ERROR"
        log(msg, "red")
        return msg


def restart_threads():
    log("Restarting all threads", "blue")
    streams_django = Stream.objects.all()

    flag_ok = True
    for stream in streams_django:
        flag_ok &= restart_thread(stream.title).find("successful") != -1

    if flag_ok:
        msg = "Threads is successfully restarted"
        log(msg, "green")
        return msg
    else:
        msg = "ERROR"
        log(msg, "red")
        return msg


def run_server():
    log("Starting server", "blue")
    app = tornado.web.Application([
        (r"/api", APIHandler),
        # (r"/stream", MJPEGHandler),
        (r"/image", ImageHandler),
    ])
    app.listen(PORT)
    log("Server is successful started", "green")
    tornado.ioloop.IOLoop.current().start()


def log(text, color="white"):
    if LOGGING:

        status = None
        if color == "cyan" or color == "white":
            status = "ALL"
        elif color == "magenta" or color == "blue":
            status = "TRACE"
        elif color == "green":
            status = "INFO"
        elif color == "yellow":
            status = "WARN"
        elif color == "red":
            status = "ERROR"
        else:
            status = None
        log_text = "[%s][%5s] - %s \n" % (str(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")), status, text)
        log_file = open("/root/django/log.txt", "a")
        log_file.write(log_text)
        log_file.close()

        print(colored(text, color))


def ilog(logs):
    print("**********")
    print(colored(logs, "cyan"))
    print("**********")


def find_thread(title):
    for thread in threading.enumerate():
        if thread.name == title:
            return thread
    return None
init_threads()
run_server()