import datetime
import json
import threading
import time
from threading import Thread
import numpy as np
import math
import cv2
import io
import os
import tornado.escape
import tornado.gen
import tornado.ioloop
import tornado.web
from PIL import Image
from termcolor import colored

from control_pane.models import Stream, History, Drone

LOGGING = True
PORT = 15152

streams = {}

no_image = Image.open("/root/django/control_pane/static/img/noimage.jpg")

logo = cv2.imread("/root/django/media/sokol.png", cv2.IMREAD_UNCHANGED)
(wH, wW) = logo.shape[:2]
scale_percent = 60 # percent of original size
width = int(wW * scale_percent / 100)
height = int(wH * scale_percent / 100)
dim = (width, height)
logo_small = cv2.resize(logo, dim, interpolation = cv2.INTER_AREA)
(wHs, wWs) = logo_small.shape[:2]
logo = cv2.resize(logo, dim, interpolation = cv2.INTER_AREA)
(wH, wW) = logo.shape[:2]
logo = np.asarray(Image.fromarray(logo).convert("RGBA"))
# logo = Image.fromarray(logo)

# load the input image, then add an extra dimension to the
# image (i.e., the alpha transparency)
# logo_small = cv2.imread("/root/django/media/sokol.png", cv2.IMREAD_UNCHANGED)

# logo = logo.crop((1,20,50,80))
#
# b = io.BytesIO()
# logo.save(b,format="jpeg")
# logo = cv2.resize(logo, (150, 80))

class Functions:
    # @staticmethod
    # def blend_transparent(face_img, overlay_t_img) :
    #     # Split out the transparency mask from the colour info
    #     overlay_img = overlay_t_img[:, :, :3]  # Grab the BRG planes
    #     overlay_mask = overlay_t_img[:, :, 3 :]  # And the alpha plane
    #
    #     # Again calculate the inverse mask
    #     background_mask = 255 - overlay_mask
    #
    #     # Turn the masks into three channel, so we can use them as weights
    #     overlay_mask = cv2.cvtColor(overlay_mask, cv2.COLOR_GRAY2BGR)
    #     background_mask = cv2.cvtColor(background_mask, cv2.COLOR_GRAY2BGR)
    #
    #     # Create a masked out face image, and masked out overlay
    #     # We convert the images to floating point in range 0.0 - 1.0
    #     face_part = (face_img * (1 / 255.0)) * (background_mask * (1 / 255.0))
    #     overlay_part = (overlay_img * (1 / 255.0)) * (overlay_mask * (1 / 255.0))
    #
    #     # And finally just add them together, and rescale it back to an 8bit integer image
    #     return np.uint8(cv2.addWeighted(face_part, 255.0, overlay_part, 255.0, 0.0))


    @staticmethod
    def threadChecker(thr, stream_id):
        while True:
            if thr.stop_trigger == False:
                time.sleep(1)
            else:
                stream_object = Stream.objects.get(id=stream_id)
                TranslationThread(stream_object)



    @staticmethod
    def updateStreamStatus(id, title, status):
        stream = Stream.objects.filter(id=id).last()
        if stream is not None:
            stream.status = status
            stream.save(update_fields=['status'])
        else:
            log("stream status with title = %s not saved" % title, "red")

    @staticmethod
    def draw_text_on_cv_frame(frame, text, position, font, font_size, color, line_size):
        # print(type(streams[title, "img"]))
        cv2.putText(np.asarray(frame), text, position, font, font_size, [0, 0, 0], line_size + 5)
        cv2.putText(np.asarray(frame), text, position, font, font_size, color, line_size)
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
            thread = Thread(target=Functions.threadChecker, args=(thread, stream_object.id,), name="thread-checker-%s" % title)
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
        self.stop_trigger = False
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
        self.stream.width = w
        self.stream.height = h
        self.stream.fps = fps
        self.stream.save(update_fields=['width', 'height', 'fps'])
        log("Connected to stream %s with parameters W=%d, H=%d, FPS=%d " % (self.stream.stream_in, w, h, fps), "green")

        if capture.isOpened():  # TODO: Сделать перезапуск
            last_packet = time.time()
            while capture.isOpened():
                ret, frame = capture.read()
                if streams[title, "stop_trigger"]:
                    streams[title, "img"] = no_image
                    break
                if ret:
                    last_packet = time.time()
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  #######################################
                    needLayers = False
                    # log("--- Frame retranslated on %s ---" % title, 'white')
                    if nn_required:
                        needLayers = True
                        time_start = time.time()

                    if telemetry_required:
                        needLayers = True
                        text = str(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S"))
                        align = h / 9
                        current_align = align
                        left_align = 20
                        font_size = 1
                        try:
                            history_record = History.objects.filter(drone_id = Drone.objects.get(camera_color_id=self.stream.id).id).last()
                        except Exception as e:
                            history_record = History.objects.filter(
                                drone_id = Drone.objects.get(camera_thermal_id = self.stream.id).id).last()
                            font_size = 0.2

                        # ********************************* Горизонтальная линия под углом ********************************************
                        c = 400
                        x = int(w / 2) - 400
                        y = int(h / 2)
                        x_roll = math.cos(float(history_record.attitude_roll)) * c
                        y_roll = math.sin(float(history_record.attitude_roll)) * c
                        if font_size == 1 :
                            # cv2.line(frame, (x, y + 1), (int(x + x_roll + 400), int(y + 1 + y_roll)), (255, 255, 255), 5)
                            cv2.line(frame, (x, y), (int(x + x_roll + 400), int(y + y_roll)), (0, 255, 0), 5)
                        else :
                            # cv2.line(frame, (int(w / 2) - 150, int(h / 2 + 1)),
                            #          (int(w / 2) - 150 + int(math.cos(float(history_record.attitude_roll)) * 150 + 150),
                            #           int(h / 2 + int(math.sin(float(history_record.attitude_roll)) * 150) + 1)),
                            #          (255, 255, 255), 5)
                            cv2.line(frame, (int(w / 2) - 100, int(h / 2)),
                                     (int(w / 2) - 100 + int(math.cos(float(history_record.attitude_roll)) * 100 + 100),
                                      int(h / 2 + int(math.sin(float(history_record.attitude_roll)) * 100))),
                                     (23, 117, 197), 5)
                        # **************************************************************************************************************
                        # ************************************************* Телеметрия *************************************************
                        Functions.draw_text_on_cv_frame(frame, text, (int(left_align), int(current_align)), cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        current_align += align
                        Functions.draw_text_on_cv_frame(frame, "Last heartbeat: " + str(history_record.last_heartbeat),
                                                        (int(left_align), int(current_align)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        current_align += align
                        Functions.draw_text_on_cv_frame(frame, "Altitude: " + str(history_record.coordinates_alt), (int(left_align), int(current_align)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        current_align += align
                        Functions.draw_text_on_cv_frame(frame, "Speed: " + str(history_record.ground_speed), (int(left_align), int(current_align)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        current_align += align
                        Functions.draw_text_on_cv_frame(frame, "Is armed: " + str(history_record.is_armed), (int(left_align), int(current_align)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        current_align += align
                        Functions.draw_text_on_cv_frame(frame, "Status: " + str(history_record.status), (int(left_align), int(current_align)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        current_align += align
                        Functions.draw_text_on_cv_frame(frame,
                                                        "Battery voltage: " + str(history_record.battery_voltage),
                                                        (int(left_align), int(current_align)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        current_align += align
                        Functions.draw_text_on_cv_frame(frame,
                                                        "Battery level: " + str(history_record.battery_level) + "%",
                                                        (int(left_align), int(current_align)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        # **************************************************************************************************************
                        # **********************************************  Логотип ******************************************************
                        def overlay_image_alpha(img, img_overlay, pos, alpha_mask):
                            """Overlay img_overlay on top of img at the position specified by
                            pos and blend using alpha_mask.

                            Alpha mask must contain values within the range [0, 1] and be the
                            same size as img_overlay.
                            """

                            x, y = pos

                            # Image ranges
                            y1, y2 = max(0, y), min(img.shape[0], y + img_overlay.shape[0])
                            x1, x2 = max(0, x), min(img.shape[1], x + img_overlay.shape[1])

                            # Overlay ranges
                            y1o, y2o = max(0, -y), min(img_overlay.shape[0], img.shape[0] - y)
                            x1o, x2o = max(0, -x), min(img_overlay.shape[1], img.shape[1] - x)

                            # Exit if nothing to do
                            if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
                                return

                            channels = img.shape[2]

                            alpha = alpha_mask[y1o:y2o, x1o:x2o]
                            alpha_inv = 1.0 - alpha

                            for c in range(channels):
                                img[y1:y2, x1:x2, c] = (alpha * img_overlay[y1o:y2o, x1o:x2o, c] +
                                                        alpha_inv * img[y1:y2, x1:x2, c])
                            return img


                        if font_size == 1:
                            frame = overlay_image_alpha(frame, logo, (int((w / 2) - (wW / 2)), 0), logo[:, :, 3] / 255.0)
                        else:
                            frame = overlay_image_alpha(frame, logo_small, (int((w / 2) - (wWs / 2)), 0), logo[:, :, 3] / 255.0)


                        # scale = 1
                        # backgroundImage = frame
                        # global logo
                        # logo = cv2.resize(np.uint8(np.asarray(logo)), (0, 0), fx=scale, fy=scale)
                        # logo = np.uint8(np.asarray(logo))
                        # # logo = cv2.resize(logo, (0, 0), fx=scale, fy=scale)
                        # hHH, wWW, _ = logo.shape  # Size of foreground
                        # pos = (int((w / 2) - (wWW / 2)), 0)
                        # rows, cols, _ = backgroundImage.shape  # Size of background Image
                        # y, x = pos[0], pos[1]  # Position of foreground/overlayImage image
                        #
                        # # loop over all pixels and apply the blending equation
                        # for i in range(hHH):
                        #     for j in range(wWW):
                        #         if x + i >= rows or y + j >= cols:
                        #             continue
                        #         alpha = float(logo[i][j][2] / 255.0)  # read the alpha channel
                        #         backgroundImage[x + i][y + j] = alpha * logo[i][j][:1] + (1 - alpha) * \
                        #                                         backgroundImage[x + i][y + j]
                        # frame = backgroundImage





                        # bwidth, bheight = frame.shape[:2]
                        # if w > 500:
                        #     fwidth, fheight = logo.shape[:2]
                        # else:
                        #     fwidth, fheight = logo_small.shape[:2]
                        # if w > 500 :
                        #     # frame[:fwidth, int(bheight / 2 + (fheight / 2)) - fheight:int(bheight / 2 + (fheight / 2))] = logo[:]  # в левый верхний
                        #     frame[:fwidth, bheight - fheight :] = logo[:]  # в левый верхний
                        # else:
                        #     frame[:fwidth, bheight - fheight :] = logo_small[:]  # в левый верхний
                        # frame[bwidth - fwidth:, :fheight] = logo[:]  # в левый нижний
                        # frame[bwidth - fwidth:, bheight - fheight :] = logo[:]  # в правый нижний

                        # ***************************************************************************************************************
                        # *************************************************** Compass ***************************************************
                        # Круг
                        cv2.circle(frame, (int((w / 2) + (w / 3)), int((h / 2) + (h / 3))), int(h / 9),
                                   (255, 255, 255), 6)
                        cv2.circle(frame, (int((w / 2) + (w / 3)), int((h / 2) + (h / 3))), int(h / 10),
                                       (50, 0, 255), 6)


                        # Направление обзора
                        c = int(h / 10)
                        x = int((w / 2) + (w / 3))
                        y = int((h / 2) + (h / 3))

                        x_roll = math.cos(float((history_record.heading + 270) * np.pi / 180)) * c
                        y_roll = math.sin(float((history_record.heading + 270) * np.pi / 180)) * c

                        x_n_roll = math.cos(float(270 * np.pi / 180)) * c
                        y_n_roll = math.sin(float(270 * np.pi / 180)) * c

                        x_s_roll = math.cos(float(450 * np.pi / 180)) * c
                        y_s_roll = math.sin(float(450 * np.pi / 180)) * c

                        x_s_roll = math.cos(float(450 * np.pi / 180)) * c
                        y_s_roll = math.sin(float(450 * np.pi / 180)) * c

                        x_w_roll = math.cos(float(540 * np.pi / 180)) * c
                        y_w_roll = math.sin(float(540 * np.pi / 180)) * c

                        x_e_roll = math.cos(float(360 * np.pi / 180)) * c
                        y_e_roll = math.sin(float(360 * np.pi / 180)) * c

                        Functions.draw_text_on_cv_frame(frame,
                                                        "N",
                                                        (int(x + x_n_roll), int(y + y_n_roll)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        Functions.draw_text_on_cv_frame(frame,
                                                        "S",
                                                        (int(x + x_s_roll), int(y + y_s_roll)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        Functions.draw_text_on_cv_frame(frame,
                                                        "W",
                                                        (int(x + x_w_roll), int(y + y_w_roll)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        Functions.draw_text_on_cv_frame(frame,
                                                        "E",
                                                        (int(x + x_e_roll), int(y + y_e_roll)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [255, 255, 255], 2)
                        Functions.draw_text_on_cv_frame(frame,
                                                        "^",
                                                        (int(x + x_roll), int(y + y_roll)),
                                                        cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                        [0, 255, 0], 3)
                        streams[title, "img"] = frame



                    # Functions.overlay_transparent(np.uint8(np.asarray(frame)), np.uint8(np.asarray(logo)), w / 2, h / 2, w, h)

                    if needLayers == False:
                        streams[title, "img"] = frame

                    # /tmp/streams/{title}
                else:
                    if time.time() - last_packet > 10:
                        self.stop_trigger = True
                        log("Stream %s is not available" % title, "red")
                        time.sleep(1)
                        break
        else:
            self.stop_trigger = True
            log("Stream %s is not available" % title, "red")
        capture.release()
        streams[title, "stop_trigger"] = True
        log("Thread %s is not alive" % title, "red")



class APIHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        log(self.request, 'cyan')
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
        log(self.request, 'cyan')
        last_image = ""
        while True:
            interval = 0.1
            if self.served_image_timestamp + interval < time.time():
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
            else:
                yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)


class MJPEGHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        log(self.request, 'cyan')
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
        log(self.request, 'cyan')
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
        (r"/xeoma", MJPEGXeomaHandler),
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
