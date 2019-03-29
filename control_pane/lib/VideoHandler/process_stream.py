import datetime
import json
import threading
import time
from threading import Thread
import numpy as np

import cv2
import io
import os
import tornado.escape
import tornado.gen
import tornado.ioloop
import tornado.web
from PIL import Image
from termcolor import colored

from control_pane.models import Stream

LOGGING = True
PORT = 15152

streams = {}

no_image = Image.open(os.getcwd() + "/django/control_pane/static/img/noimage.jpg")


class Functions:
    @staticmethod
    def threadChecker(thr, title):
        while thr['stop_trigger']

    @staticmethod
    def updateStreamStatus(id, title, status):
        stream = Stream.objects.filter(id=id).last()
        if stream is not None:
            stream.status = status
            stream.save(update_fields=['status'])
        else:
            log("stream status with title = %s not saved" % title, "red")

    @staticmethod
    def draw_text_on_cv_frame(title, text, position, font, font_size, color, line_size):
        # print(type(streams[title, "img"]))
        cv2.putText(np.asarray(streams[title, "img"]), text, position, font, font_size, [0, 0, 0], line_size + 5)
        cv2.putText(np.asarray(streams[title, "img"]), text, position, font, font_size, color, line_size)
        return streams[title, "img"]
        # return frame

    @staticmethod
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

    @staticmethod
    def write_image(tornadoself, title):
        o = io.BytesIO()
        try:
            img = Image.fromarray(streams[title, "img"])
        # Если обычная картинка, то тут маленькие танцы с конвертами
        except:
            img = Image.fromarray(np.uint8(np.asarray(streams[title, "img"])))

        img.save(o, format="JPEG")

        s = o.getvalue()

        tornadoself.write("--boundarydonotcross\n")
        tornadoself.write("Content-type: image/jpeg\r\n")
        tornadoself.write("Content-length: %s\r\n\r\n" % len(s))
        tornadoself.write(s)

    @staticmethod
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


class StreamControl:
    @staticmethod
    def init_thread(title):
        log("Initializing thread %s" % title, "blue")
        streams[title, 'img'] = no_image
        streams[title, "stop_trigger"] = False
        log("Thread %s successfully initialized" % title, "green")

    @staticmethod
    def init_threads():
        log("Initializing all threads", "blue")
        streams_django = Stream.objects.all()
        for stream in streams_django:
            StreamControl.init_thread(stream.title)

    @staticmethod
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

            thread = TranslationThread(stream_object)
            thread.start()
            thread = Thread(target=Functions.threadChecker, args=(thread, title,), name="thread-checker-%s" % title)
            thread.start()

            msg = "Thread %s is successfully started" % title
            log(msg, "green")
            time.sleep(0.2)  # DELAY
            return msg
        else:
            msg = "Thread %s is already started" % title
            log(msg, "yellow")
            return msg

    @staticmethod
    def start_threads():
        log("Starting all threads", "blue")
        streams_django = Stream.objects.all().order_by('title')

        flag_ok = True
        for stream in streams_django:
            flag_ok &= (StreamControl.start_thread(stream.title).find(
                "successful") != -1 or StreamControl.start_thread(stream.title).find(
                "already") != -1)

        if flag_ok:
            msg = "Threads is successfully started"
            log(msg, "green")
            return msg
        else:
            msg = "ERROR"
            log(msg, "red")
            return msg

    @staticmethod
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

    @staticmethod
    def stop_threads():
        log("Stopping all threads", "blue")
        streams_django = Stream.objects.all()

        for stream in streams_django:
            StreamControl.stop_thread(stream.title)

        msg = "Threads is successfully stopped"
        log(msg, "green")
        return msg

    @staticmethod
    def restart_thread(title):
        log("Restarting thread %s" % title, "blue")

        StreamControl.stop_thread(title)
        restarted_thread = find_thread(title)
        if restarted_thread is not None:
            while restarted_thread.is_alive():
                time.sleep(0.1)  # DO NOTHING

        if StreamControl.start_thread(title).find("successful") != -1:
            msg = "Thread %s is successfully restarted" % title
            log(msg, "green")
            return msg
        else:
            msg = "ERROR"
            log(msg, "red")
            return msg

    @staticmethod
    def restart_threads():
        log("Restarting all threads", "blue")
        streams_django = Stream.objects.all()

        flag_ok = True
        for stream in streams_django:
            flag_ok &= StreamControl.restart_thread(stream.title).find("successful") != -1

        if flag_ok:
            msg = "Threads is successfully restarted"
            log(msg, "green")
            return msg
        else:
            msg = "ERROR"
            log(msg, "red")
            return msg

class TranslationThread(Thread):
    def __init__(self, stream, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.name = stream.title
        self.stream = stream
    def run(self):
        title = self.stream.title
        capture = cv2.VideoCapture(self.stream.stream_in)
        h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(capture.get(cv2.CAP_PROP_FPS))
        while h == 0 and w == 0 and fps == 0:
            capture = cv2.VideoCapture(self.stream.stream_in)
            h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            fps = int(capture.get(cv2.CAP_PROP_FPS))
            time.sleep(1);
        nn_required = self.stream.nn_required
        telemetry_required = self.stream.telemetry_required
        self.stream.objects.filter(title=title).update(width=w, height=h, fps=fps)
        log("Connected to stream %s with parameters W=%d, H=%d, FPS=%d " % (self.stream.stream_in, w, h, fps), "green")

        if capture.isOpened():  # TODO: Сделать перезапуск
            while capture.isOpened():
                ret, frame = capture.read()
                if streams[title, "stop_trigger"]:
                    streams[title, "img"] = no_image
                    break
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  #######################################
                    streams[title, "img"] = frame
                    # log("--- Frame retranslated on %s ---" % title, 'white')
                    if nn_required:
                        time_start = time.time()
                        # # results = model.detect([frame], verbose=1)
                        # time_detect = time.time()
                        #
                        # # r = results[0]
                        # # frame = display_instances(
                        # #     frame, r["rois"], r["masks"], r["class_ids"], class_names, r["scores"]
                        # # )
                        #
                        # time_display_instance = time.time()
                        #
                        # log("--- Frame detected on %s ---" % title, 'white')
                        # log("%.2f + %.2f = %.2f" % (time_detect - time_start,
                        #                             time_display_instance - time_detect,
                        #                             time_display_instance - time_start), 'white')
                        # for i in range(len(r["class_ids"])):
                        #     log("I see \"%s\" with accuracy ~%s on %s" % (
                        #         str(class_names[r["class_ids"][i]]), str(int(r["scores"][i] * 1000) / 10),
                        #         title) + "%", 'magenta')

                    if telemetry_required:
                        text = str(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S"))
                        Functions.draw_text_on_cv_frame(title, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                                        [255, 255, 255], 2)

                    # /tmp/streams/{title}

                else:
                    log("Stream %s is not available" % title, "red")
                    time.sleep(1)
        capture.release()
        streams[title, "stop_trigger"] = True
        log("Thread %s is not alive" % title, "red")



class APIHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        Functions.write_header(self)

        action = self.get_argument("action", None)
        title = self.get_argument("title", None)
        obj = self.get_argument("obj", None)
        stream_id = self.get_argument("stream_id", None)
        ilog("action - %s, title - %s, obj - %s" % (action, title, obj))

        if action == "start":
            Functions.updateStreamStatus(stream_id, title, True)
            Functions.write_status(self, StreamControl.start_thread(title))
        elif action == "stop":
            Functions.updateStreamStatus(stream_id, title, False)
            Functions.write_status(self, StreamControl.stop_thread(title))
        elif action == "restart":
            Functions.updateStreamStatus(stream_id, title, True)
            Functions.write_status(self, StreamControl.restart_thread(title))
        elif action == "start-all":
            Functions.write_status(self, StreamControl.start_threads())
        elif action == "stop-all":
            Functions.write_status(self, StreamControl.stop_threads())
        elif action == "restart-all":
            Functions.write_status(self, StreamControl.restart_threads())

        elif action == "create":
            json_parsed = json.loads(obj)
            new_stream = Stream.create_json(json_parsed)
            new_stream.init()
            log(new_stream.to_str(), "yellow")

            new_stream.save()

            StreamControl.init_thread(new_stream.title)
            Functions.write_status(self, "Stream successfully created")
            log("New stream successfully created", "green")
            log(new_stream.to_str(), "green")

        elif action == "delete":
            stream = Stream.objects.filter(title=title).last()
            if stream is not None:
                stream.delete()
                log("Stream %s successfully deleted" % title, "green")
                Functions.write_status(self, "Stream %s successfully deleted" % title)
            else:
                log("Stream with title %s does not exist" % title, "red")
                Functions.write_status("Stream with title %s does not exist" % title)

        elif action == "update":
            json_parsed = json.loads(obj)
            stream = Stream.objects.filter(id=stream_id).last()
            if stream != None:
                stream.stream_in = json_parsed['stream_in']
                stream.uid = json_parsed['uid']
                stream.protocol = json_parsed['protocol']
                stream.record_path = json_parsed['record_path']
                stream.tmp_image_path = json_parsed['tmp_image_path']
                stream.nn_required = json_parsed['nn_required']
                stream.telemetry_required = json_parsed['telemetry_required']
                stream.save()

                # Если есть живой поток, то перезапуск, иначе ничего
                if find_thread(stream.title):
                    StreamControl.restart_thread(stream.title)

                log("Stream successfully updated", "green")
                Functions.write_status(self, "Stream successfully updated")
            else:
                log("Unexpected stream with id - %s" % stream_id, "red")

        else:
            log("Unexpected action - %s" % action, "red")

    def options(self):
        self.set_status(204)
        self.finish()


class MJPEGXeomaHandler(tornado.web.RequestHandler):
    def head(self):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        self.set_header('Pragma', 'no-cache')
        self.set_header('Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
        self.set_header('Connection', 'close')

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        ioloop = tornado.ioloop.IOLoop.current()
        title = self.get_argument("title", None)
        self.served_image_timestamp = time.time()
        last_image = ""
        while True:
            # interval = 0.1
            # if self.served_image_timestamp + interval < time.time():
            o = io.BytesIO()
            try:
                img = Image.fromarray(streams[title, "img"])
            # Если обычная картинка, то тут маленькие танцы с конвертами
            except:
                img = Image.fromarray(np.uint8(np.asarray(streams[title, "img"])))
            img.save(o, format="JPEG")
            s = o.getvalue()

            self.write("--jpgboundary")
            self.write("Content-length: %s\r\n\r\n" % len(s))
            self.write(s)
            self.served_image_timestamp = time.time()
            yield tornado.gen.Task(self.flush)
            # else:
            #     yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)


class MJPEGHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        title = self.get_argument("title", None)
        title = title.split('?')[0]
        Functions.write_header(self)
        while True:
            Functions.write_image(self, title)
            yield tornado.gen.Task(self.flush)  # I have no idea why it works

    def options(self):
        # no body
        self.set_status(204)
        self.finish()


class ImageHandler(tornado.web.RequestHandler):
    def get(self):
        title = self.get_argument("title", None)
        Functions.write_header(self)
        Functions.write_image(self, title)

    def options(self):
        self.set_status(204)
        self.finish()


def run_server():
    log("Starting server", "blue")

    app = tornado.web.Application([
        (r"/api", APIHandler),
        (r"/stream", MJPEGHandler),
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
