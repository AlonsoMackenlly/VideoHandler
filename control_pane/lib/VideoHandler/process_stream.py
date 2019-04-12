import os
import datetime
import json
import threading
import time
from threading import Thread
import numpy as np
import math
import cv2
import io
import tornado.escape
import tornado.gen
import tornado.ioloop
import tornado.web
import imutils
from PIL import Image
from termcolor import colored
from PIL.JpegImagePlugin import JpegImageFile
from control_pane.models import Stream, History, Drone
# TODO: Кириллица
LOGGING = True
PORT = 15152
CONFIDENCE = 0.1
THRESHOLD = 0.3
streams = {}
hhh = 1
no_image = Image.open("/root/django/control_pane/static/img/noimage.jpg")

# logo = cv2.imread("/root/django/media/sokol.png", cv2.IMREAD_UNCHANGED)
# print(logo)
# (wH, wW) = logo.shape[:2]
# dim = (int(wW * 0.6), int(wH * 0.6))

# # logo_small = cv2.resize(logo, dim, interpolation=cv2.INTER_AREA)
# logo_small = cv2.resize(logo, (0, 0), fx=0.25, fy=0.25)

# (wHs, wWs) = logo_small.shape[:2]
# logo = cv2.resize(logo, dim, interpolation=cv2.INTER_AREA)
# (wH, wW) = logo.shape[:2]
# logo = np.asarray(Image.fromarray(logo).convert("RGBA"))
# ********************************************* Подключение cv моделей (YOLOv3-tiny) *****************************************
# load the COCO class labels our YOLO model was trained on
# LABELS = open("/root/django/control_pane/lib/VideoHandler/yolo-coco/coco.names").read().strip().split("\n")
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
    "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
    "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
    "sofa", "train", "tvmonitor"]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))
# initialize a list of colors to represent each possible class label
np.random.seed(42)
# COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
#     dtype="uint8")

# load our YOLO object detector trained on COCO dataset (80 classes)
# and determine only the *output* layer names that we need from YOLO
print("[INFO] loading YOLO from disk...")
net = cv2.dnn.readNetFromCaffe("/root/django/control_pane/lib/VideoHandler/MobileNetSSD_deploy.prototxt.txt", "/root/django/control_pane/lib/VideoHandler/MobileNetSSD_deploy.caffemodel")
# net = cv2.dnn.readNetFromDarknet("/root/django/control_pane/lib/VideoHandler/yolo-coco/yolov3-tiny.cfg", "/root/django/control_pane/lib/VideoHandler/yolo-coco/yolov3-tiny.weights")
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
# *****************************************************************************************************************************
class DrawingFunctions:
    k = 0
    font_size = 0
    line_size = 0
    delta_line = 0
    @staticmethod
    def drawCenterDistance(frame, w, h, distance):
        DrawingFunctions.draw_text_on_cv_frame(frame, distance + ' m.', (int(w / 2), int(h / 2)),
                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size + 3, [255, 255, 255], DrawingFunctions.line_size,
                                               DrawingFunctions.delta_line)
    @staticmethod
    def draw_text_on_cv_frame(frame, text, position, font, font_size, color, line_size):
        # print(type(streams[title, "img"]))
        cv2.putText(np.asarray(frame), text, position, font, font_size, [0, 0, 0], line_size + 5)
        cv2.putText(np.asarray(frame), text, position, font, font_size, color, line_size)
        # return frame
    @staticmethod
    def drawHorizontalRotation(frame, w, h, attitude_roll, c):
        ''' Рисует горизонтальную линию, угол поворота коптера по оси roll
            * frame = Картинка
            * w = Ширина фрейма
            * h = Высота фрейма
            * attitude_roll = Угол в радианах (горизонтальное смещение коптера)
            * c = длина отрезка в px
        '''
        x = int(w / 2 - c)
        y = int(h / 2)
        x_roll = math.cos(float(attitude_roll)) * c
        y_roll = math.sin(float(attitude_roll)) * c

        x_roll_until = int(math.cos(float(attitude_roll) * (-1)) * c)
        y_roll_until = int(math.sin(float(attitude_roll) * (-1)) * c)

        cv2.line(frame, (x_roll_until, y_roll_until), (int(x + x_roll + c), int(y + y_roll)), (207, 107, 70),
                 int(8 / DrawingFunctions.k ** DrawingFunctions.k))
        cv2.circle(frame, (int(w / 2), int(h / 2)), int(c + 50 / DrawingFunctions.k ** DrawingFunctions.k), (188, 188, 188), int(2 / DrawingFunctions.k),
                   lineType=8)
        return frame
    @staticmethod
    def drawTelemetry(frame, title, w, h, history_record):
        ''' Накладывает слой телеметрии коптера
            * frame = Картинка
            * title = Название видеопотока
            * w = Ширина фрейма
            * h = Высота фрейма
            * history_record = Объект записи истории
            * k = Коэффициент масштабирования
        '''

        DrawingFunctions.draw_text_on_cv_frame(frame, title, (int(20 / DrawingFunctions.k), int(30 / DrawingFunctions.k)),
                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size, [255, 255, 255], DrawingFunctions.line_size,
                                               DrawingFunctions.delta_line)
        text = str(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S"))
        DrawingFunctions.draw_text_on_cv_frame(frame, text, (int(150 / DrawingFunctions.k), int(30 / DrawingFunctions.k)),
                                               cv2.FONT_HERSHEY_DUPLEX, DrawingFunctions.font_size, [255, 255, 255], DrawingFunctions.line_size,
                                               DrawingFunctions.delta_line)
        DrawingFunctions.draw_text_on_cv_frame(frame, "Status: " + str(history_record.status),
                                               (int(w - 200 / DrawingFunctions.k), int(30 / DrawingFunctions.k)), cv2.FONT_HERSHEY_SIMPLEX,
                                               DrawingFunctions.font_size, [255, 255, 255], DrawingFunctions.line_size, DrawingFunctions.delta_line)
        DrawingFunctions.draw_text_on_cv_frame(frame,
                                               "Lat: " + str(history_record.coordinates_lat) + ", Lon: " + str(
                                                   history_record.coordinates_lon) + ", Altitude : " + str(
                                                   history_record.coordinates_alt),
                                               (int(20 / DrawingFunctions.k), int(h - 50 / DrawingFunctions.k)), cv2.FONT_HERSHEY_SIMPLEX,
                                               DrawingFunctions.font_size, [255, 255, 255], DrawingFunctions.line_size, DrawingFunctions.delta_line)

        DrawingFunctions.draw_text_on_cv_frame(frame, "Speed: " + str(
            history_record.ground_speed) + "; Battery: " + str(
            history_record.battery_voltage) + "V" + ", " + str(
            history_record.battery_level) + "%; " + "Last heartbeat: " + str(
            history_record.last_heartbeat) + " s.",
                                               (int(20 / DrawingFunctions.k), int(h - 20 / DrawingFunctions.k)),
                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size,
                                               [255, 255, 255], DrawingFunctions.line_size, DrawingFunctions.delta_line)
        return frame
    @staticmethod
    def drawCompass(frame, w, h, heading):
        # Круг
        cv2.circle(frame, (int((w / 2) + (w / 2.5)), int((h / 2) + (h / 3))), int(h / 9),
                   (255, 255, 255), 6)
        cv2.circle(frame, (int((w / 2) + (w / 2.5)), int((h / 2) + (h / 3))), int(h / 10),
                   (207, 107, 70), 6)

        # Направление обзора
        c = int(h / 10)
        x = int((w / 2) + (w / 2.5))
        y = int((h / 2) + (h / 3))

        x_roll = math.cos(float((heading + 270) * np.pi / 180)) * c
        y_roll = math.sin(float((heading + 270) * np.pi / 180)) * c

        # + и - нужны для того, чтобы буквы были ровно по середине
        x_n_roll = math.cos(float(270 * np.pi / 180)) * c - 3
        y_n_roll = math.sin(float(270 * np.pi / 180)) * c + 3

        x_s_roll = math.cos(float(450 * np.pi / 180)) * c - 3
        y_s_roll = math.sin(float(450 * np.pi / 180)) * c + 3

        x_w_roll = math.cos(float(540 * np.pi / 180)) * c - 3
        y_w_roll = math.sin(float(540 * np.pi / 180)) * c + 3

        x_e_roll = math.cos(float(360 * np.pi / 180)) * c - 3
        y_e_roll = math.sin(float(360 * np.pi / 180)) * c + 3

        DrawingFunctions.draw_text_on_cv_frame(frame, "N", (int(x + x_n_roll), int(y + y_n_roll)),
                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size, [255, 255, 255], DrawingFunctions.line_size,
                                               DrawingFunctions.delta_line)
        DrawingFunctions.draw_text_on_cv_frame(frame, "S", (int(x + x_s_roll), int(y + y_s_roll)),
                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size, [255, 255, 255], DrawingFunctions.line_size,
                                               DrawingFunctions.delta_line)
        DrawingFunctions.draw_text_on_cv_frame(frame, "W", (int(x + x_w_roll), int(y + y_w_roll)),
                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size, [255, 255, 255], DrawingFunctions.line_size,
                                               DrawingFunctions.delta_line)
        DrawingFunctions.draw_text_on_cv_frame(frame, "E", (int(x + x_e_roll), int(y + y_e_roll)),
                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size, [255, 255, 255], DrawingFunctions.line_size,
                                               DrawingFunctions.delta_line)
        DrawingFunctions.draw_text_on_cv_frame(frame, "^", (int(x + x_roll), int(y + y_roll)),
                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size, [0, 255, 0], DrawingFunctions.line_size + 1,
                                               DrawingFunctions.delta_line)
        return frame
class Functions:
    @staticmethod
    def getCenterDistance(GimbalYDegree, Altitude):
        return Altitude * math.tan(GimbalYDegree)
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
    def thread_checker(thr, stream_id):
        while True:
            try:
                if thr != None:
                    if not thr.stop_trigger:
                        time.sleep(1)
                    else:
                        stream_object = Stream.objects.get(id=stream_id)
                        thr = TranslationThread(stream_object).start()
                else:
                    stream_object = Stream.objects.get(id=stream_id)
                    thr = TranslationThread(stream_object).start()
            except Exception as e:
                log (thr, 'red')
                log(e, 'red')
                time.sleep(1)

    @staticmethod
    def updateStreamStatus(id, title, status):
        stream = Stream.objects.filter(id=id).last()
        if stream is not None:
            stream.status = status
            stream.save(update_fields=['status'])
        else:
            log("stream status with title = %s not saved" % title, "red")

    @staticmethod
    def write_header(tornado_self):
        tornado_self.send_response(200)
        tornado_self.set_header("Access-Control-Allow-Origin", "*")
        tornado_self.set_header("Access-Control-Allow-Headers", "*")
        tornado_self.set_header("Access-Control-Allow-Methods", "*")
        tornado_self.set_header("Access-Control-Allow-Credentials", "true")
        
        tornado_self.set_header("Cache-Control",
                                "no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0")
        tornado_self.set_header("Connection", "close")
        tornado_self.set_header("Content-Type", "multipart/x-mixed-replace;boundary=--boundarydonotcross")
        tornado_self.set_header("Expires", "Mon, 3 Jan 2000 12:34:56 GMT")
        tornado_self.set_header("Pragma", "no-cache")
        # print("+++++++++++++++")
        tornado_self.end_headers()
        # print("+++++++++++++++")
    @staticmethod
    def write_image(tornado_self, title):
        # o = io.BytesIO()
        try:
            ret, jpeg = cv2.imencode('.jpg', streams[title, "img"], [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            # img = Image.fromarray(streams[title, "img"])
        # Если обычная картинка, то тут маленькие танцы с конвертами
        except:
            ret, jpeg = cv2.imencode('.jpg', np.asarray(streams[title, "img"]), [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            # img = Image.fromarray(np.uint8(np.asarray(streams[title, "img"])))

        
        # img.save(o, format="JPEG")
        # o.seek(0)
        # s = o.getvalue()
        tornado_self.write("--boundarydonotcross\n")
        tornado_self.write("Content-type: image/jpeg\r\n")
        tornado_self.write("Content-length: %s\r\n\r\n" % len(jpeg.tobytes()))
        tornado_self.write(jpeg.tobytes())
        # log(str(len(s)), 'cyan')
        # log(str(len(tornado_self.body)), 'cyan')

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

            thread = Thread(target=Functions.thread_checker, args=(thread, stream_object.id,),
                            name="thread-checker-%s" % title)
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

class DetectionFrame(Thread):
    def __init__(self, stream, capture, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.name = stream.title
        self.stream = stream
        self.stop_trigger = False
        self.capture = capture
    def run(self):
        capture = self.capture
        title = self.name
        streams[self.name, 'detections'] = { }
        t = ''
        t_restart = time.time()
        t_record = time.time()
        writer = None
        while True:
            frame = streams[self.name, 'img']
            if type(frame) != JpegImageFile:
                h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                fps = int(capture.get(cv2.CAP_PROP_FPS))
                try:
                    prop = cv2.cv.CV_CAP_PROP_FRAME_COUNT if imutils.is_cv2() \
                        else cv2.CAP_PROP_FRAME_COUNT
                    total = int(capture.get(prop))
                    print("[INFO] {} total frames in video".format(total))

                # an error occurred while trying to determine the total
                # number of frames in the video file
                except Exception as e:
                    log(e, "red")
                    print("[INFO] could not determine # of frames in video")
                    print("[INFO] no approx. completion time can be provided")
                    total = -1

                # construct a blob from the input frame and then perform a forward
                # pass of the YOLO object detector, giving us our bounding boxes
                # and associated probabilities
                blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
                net.setInput(blob)
                start = time.time()
                detections = net.forward()
                end = time.time()
                # initialize our lists of detected bounding boxes, confidences,
                # and class IDs, respectively
                boxes = []
                confidences = []
                classIDs = []

                for i in np.arange(0, detections.shape[2]):
                    streams[title, 'detections'][i] = {
                        'color': '',
                        'text': '',
                        'rectangleXY': '',
                        'rectangleXYend': '',
                        'x': '',
                        'y': '',
                        'w': '',
                        'h': '',
                        't': ''
                    }
                    confidence = detections[0, 0, i, 2]

                    # filter out weak detections by ensuring the `confidence` is
                    # greater than the minimum confidence
                    # print(img)
                    if confidence > CONFIDENCE:
                        t = time.time()
                        # extract the index of the class label from the
                        # `detections`, then compute the (x, y)-coordinates of
                        # the bounding box for the object
                        idx = int(detections[0, 0, i, 1])
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (startX, startY, endX, endY) = box.astype("int")

                        # draw the prediction on the frame
                        label = CLASSES[idx]
                        if label == "person":
                            label = "HUMAN"
                        y = startY - 15 if startY - 15 > 15 else startY + 15
                        streams[title, 'detections'][i]['x'] = startX; streams[title, 'detections'][i]['y'] = y; streams[title, 'detections'][i]['w'] = (endX - startX); streams[title, 'detections'][i]['h'] = (endY - startY)
                        streams[title, 'detections'][i]['color'] = COLORS[idx]
                        streams[title, 'detections'][i]['text'] = label
                        streams[title, 'detections'][i]['rectangleXY'] = (startX, startY)
                        streams[title, 'detections'][i]['rectangleXYend'] = (endX, endY)
                        streams[title, 'detections'][i]['t'] = time.time()
                elap = (end - start)
                print("[INFO] single frame took {:.4f} seconds".format(elap))
                print("[INFO] estimated total time to finish: {:.4f}".format(
                    elap * total))

                if type(t) is not str:
                    if time.time() - t > 5:
                        streams[self.name, 'detections'] = { }
class TranslationThread(Thread):
    def __init__(self, stream, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.name = stream.title
        self.stream = stream
        self.stop_trigger = False

    def run(self):
        title = self.stream.title
        capture = cv2.VideoCapture(self.stream.stream_in)
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG')) #XVID cv2.VideoWriter_fourcc(*'MJPG')
        capture.set(cv2.CAP_PROP_FPS, 25) #XVID
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(capture.get(cv2.CAP_PROP_FPS))
        while h == 0 and w == 0 and fps == 0:
            capture = cv2.VideoCapture(self.stream.stream_in) #"http://172.19.1.10/tmpfs/snap.jpg?usr=admin&pwd=admin"
            h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            fps = int(capture.get(cv2.CAP_PROP_FPS))
            time.sleep(5)

        nn_required = self.stream.nn_required
        if nn_required == True:
            nn_detection = DetectionFrame(self.stream, capture)
            nn_detection.start()
        telemetry_required = self.stream.telemetry_required 
        record_required = self.stream.record_required
        self.stream.width = w
        self.stream.height = h
        self.stream.fps = fps
        self.recordIsOff = False
        self.stream.save(update_fields=['width', 'height', 'fps'])
        log("Connected to stream %s with parameters W=%d, H=%d, FPS=%d " % (self.stream.stream_in, w, h, fps), "green")

        if capture.isOpened():  # TODO: Сделать перезапуск
            last_packet = time.time()
            i = time.time()
            t_record = time.time()
            t_restart = time.time()
            writer = None
            global hhh
            t_db = time.time()
            history_record = ""
            while capture.isOpened():
                # hhh = hhh + 1
                # print("handler hhh = " + str(hhh))
                #cv2.imread("http://10.8.0.101/tmpfs/snap.jpg?usr=admin&pwd=admin")
                ret, frame = capture.read()
                if streams[title, "stop_trigger"]:
                    streams[title, "img"] = no_image
                    break
                if ret:
                    last_packet = time.time()
                    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # ######################################

                    # frame = cv2.resize(frame, (640, 480))
                    # w = 640
                    # h = 480
                    need_layers = False
                    # log("--- Frame retranslated on %s ---" % title, 'white')
                    # if nn_required:

                    if nn_required:
                        overlay = frame.copy()
                        try:
                            for i in streams[title, 'detections']:
                                # if time.time() - streams[title, 'detections'][i]['t'] < 3:
                                xx = streams[title, 'detections'][i]['x']
                                yy = streams[title, 'detections'][i]['y']
                                cv2.rectangle(overlay, streams[title, 'detections'][i]['rectangleXY'], streams[title, 'detections'][i]['rectangleXYend'], streams[title, 'detections'][i]['color'], cv2.FILLED)
                                cv2.putText(overlay, streams[title, 'detections'][i]['text'], (xx, yy - 5), cv2.FONT_HERSHEY_TRIPLEX, 1, [0, 0, 0], 7)
                                cv2.putText(overlay, streams[title, 'detections'][i]['text'], (xx, yy - 5), cv2.FONT_HERSHEY_TRIPLEX, 1, streams[title, 'detections'][i]['color'], 2)  #(52, 182, 170)
                            cv2.addWeighted(overlay, 0.5, frame, 1 - 0.5, 0, frame)
                        except Exception as e:
                            time.sleep(0.00001)
                        need_layers = True
                        streams[title, 'img'] = frame
                    if telemetry_required:
                        # Коэффициент перевода текста и графики в более приятный вид для низких разрешений
                        if w <= 1024:
                            k = 2
                        elif w <= 1920:
                            k = 1
                        else:
                            k = 0.7


                        DrawingFunctions.k = k
                        DrawingFunctions.font_size = 0.7 / k
                        DrawingFunctions.line_size = int(2 / k)
                        DrawingFunctions.delta_line = int(5 / k)

                        need_layers = True
                        align = h / 11
                        current_align = align
                        if time.time() - t_db > 1:
                            try:
                                history_record = History.objects.filter(
                                    drone_id=Drone.objects.get(camera_color_id=self.stream.id).id).last()
                            except Exception as e:
                                history_record = History.objects.filter(
                                    drone_id=Drone.objects.get(camera_thermal_id=self.stream.id).id).last()
                            t_db = time.time()
                        else:
                            if type(history_record) is str:
                                ilog(self.stream.id)
                                try:
                                    history_record = History.objects.filter(drone_id=Drone.objects.get(camera_color_id=self.stream.id).id).last()
                                except Exception as e:
                                    history_record = History.objects.filter(drone_id=Drone.objects.get(camera_thermal_id=self.stream.id).id).last()

                        ''' 
                        ****************************** Горизонтальная линия под углом ******************************
                        '''
                        c = 250 / k ** k
                        # frame = DrawingFunctions.drawHorizontalRotation(frame, w, h, history_record.attitude_roll, c)
                        x = int(w / 2 - c)
                        y = int(h / 2)
                        x_roll = math.cos(float(history_record.attitude_roll)) * c
                        y_roll = math.sin(float(history_record.attitude_roll)) * c

                        x_roll_until = int(math.cos(float(history_record.attitude_roll) * (-1)) * c)
                        y_roll_until = int(math.sin(float(history_record.attitude_roll) * (-1)) * c)

                        cv2.line(frame, (x, y), (int(x + x_roll + c), int(y + y_roll)),
                                 (207, 107, 70),
                                 int(8 / DrawingFunctions.k ** DrawingFunctions.k))
                        cv2.circle(frame, (int(w / 2), int(h / 2)),
                                   int(c + 50 / DrawingFunctions.k ** DrawingFunctions.k), (188, 188, 188),
                                   int(2 / DrawingFunctions.k),
                                   lineType=8)
                        ''' 
                        ****************************** Телеметрия ******************************
                        '''
                        # frame = DrawingFunctions.drawTelemetry(frame, self.name, w, h, history_record)
                        DrawingFunctions.draw_text_on_cv_frame(frame, title, (
                        int(20 / DrawingFunctions.k), int(30 / DrawingFunctions.k)),
                                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size,
                                                               [255, 255, 255], DrawingFunctions.line_size)
                        text = str(datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S"))
                        DrawingFunctions.draw_text_on_cv_frame(frame, text, (
                        int(150 / DrawingFunctions.k), int(30 / DrawingFunctions.k)),
                                                               cv2.FONT_HERSHEY_DUPLEX, DrawingFunctions.font_size,
                                                               [255, 255, 255], DrawingFunctions.line_size)
                        DrawingFunctions.draw_text_on_cv_frame(frame, "Status: " + str(history_record.status),
                                                               (int(w - 200 / DrawingFunctions.k),
                                                                int(30 / DrawingFunctions.k)), cv2.FONT_HERSHEY_SIMPLEX,
                                                               DrawingFunctions.font_size, [255, 255, 255],
                                                               DrawingFunctions.line_size)
                        DrawingFunctions.draw_text_on_cv_frame(frame,
                                                               "Lat: " + str(
                                                                   history_record.coordinates_lat) + ", Lon: " + str(
                                                                   history_record.coordinates_lon) + ", Altitude : " + str(
                                                                   history_record.coordinates_alt),
                                                               (int(20 / DrawingFunctions.k),
                                                                int(h - 50 / DrawingFunctions.k)),
                                                               cv2.FONT_HERSHEY_SIMPLEX,
                                                               DrawingFunctions.font_size, [255, 255, 255],
                                                               DrawingFunctions.line_size)

                        DrawingFunctions.draw_text_on_cv_frame(frame, "Speed: " + str(
                            history_record.ground_speed) + "; Battery: " + str(
                            history_record.battery_voltage) + "V" + ", " + str(
                            history_record.battery_level) + "%; " + "Last heartbeat: " + str(
                            history_record.last_heartbeat) + " s.",
                                                               (int(20 / DrawingFunctions.k),
                                                                int(h - 20 / DrawingFunctions.k)),
                                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size,
                                                               [255, 255, 255], DrawingFunctions.line_size)
                        '''
                        ****************************** Компас ******************************
                        '''
                        # frame = DrawingFunctions.drawCompass(frame, w, h, history_record.heading)
                        cv2.circle(frame, (int((w / 2) + (w / 2.5)), int((h / 2) + (h / 3))), int(h / 9),
                                   (255, 255, 255), 6)
                        cv2.circle(frame, (int((w / 2) + (w / 2.5)), int((h / 2) + (h / 3))), int(h / 10),
                                   (207, 107, 70), 6)

                        # Направление обзора

                        x = int((w / 2) + (w / 2.5))
                        y = int((h / 2) + (h / 3))

                        x_roll = math.cos(float((history_record.heading + 270) * np.pi / 180)) * c
                        y_roll = math.sin(float((history_record.heading + 270) * np.pi / 180)) * c

                        # + и - нужны для того, чтобы буквы были ровно по середине
                        x_n_roll = math.cos(float(270 * np.pi / 180)) * c - 3
                        y_n_roll = math.sin(float(270 * np.pi / 180)) * c + 3

                        x_s_roll = math.cos(float(450 * np.pi / 180)) * c - 3
                        y_s_roll = math.sin(float(450 * np.pi / 180)) * c + 3

                        x_w_roll = math.cos(float(540 * np.pi / 180)) * c - 3
                        y_w_roll = math.sin(float(540 * np.pi / 180)) * c + 3

                        x_e_roll = math.cos(float(360 * np.pi / 180)) * c - 3
                        y_e_roll = math.sin(float(360 * np.pi / 180)) * c + 3

                        DrawingFunctions.draw_text_on_cv_frame(frame, "N", (int(x + x_n_roll), int(y + y_n_roll)),
                                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size,
                                                               [255, 255, 255], DrawingFunctions.line_size)
                        DrawingFunctions.draw_text_on_cv_frame(frame, "S", (int(x + x_s_roll), int(y + y_s_roll)),
                                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size,
                                                               [255, 255, 255], DrawingFunctions.line_size)
                        DrawingFunctions.draw_text_on_cv_frame(frame, "W", (int(x + x_w_roll), int(y + y_w_roll)),
                                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size,
                                                               [255, 255, 255], DrawingFunctions.line_size)
                        DrawingFunctions.draw_text_on_cv_frame(frame, "E", (int(x + x_e_roll), int(y + y_e_roll)),
                                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size,
                                                               [255, 255, 255], DrawingFunctions.line_size)
                        DrawingFunctions.draw_text_on_cv_frame(frame, "^", (int(x + x_roll), int(y + y_roll)),
                                                               cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size,
                                                               [0, 255, 0], DrawingFunctions.line_size + 1)
                        '''
                        ****************************** Расстояние до центра камеры ******************************
                        '''
                        try:
                            alt = float(history_record.coordinates_alt)
                            gimbalDegree = 90 - float(history_record.gimbal_pitch_degree) * (-1)
                            distanceFloor = Functions.getCenterDistance(gimbalDegree, alt)
                            # print("**************")
                            # print(str(alt))
                            distanceFromCamera = math.sqrt((int(round(alt)) * int(round(alt))) + (int(round(float(distanceFloor))) * int(round(float(distanceFloor)))))
                            # print("==============")
                            # print(str(distanceFromCamera))
                            # DrawingFunctions.drawCenterDistance(frame, w, h, distance)
                            DrawingFunctions.draw_text_on_cv_frame(frame, str(int(distanceFromCamera)) + ' m.', (int(w / 2), int(h / 2)),
                                                                   cv2.FONT_HERSHEY_SIMPLEX,
                                                                   DrawingFunctions.font_size, [255, 255, 255],
                                                                   DrawingFunctions.line_size)
                            # cv2.line(frame, (int(w / 2), h), (int(w / 2), int(h / 2)), (0, 171, 1), 1)
                            del_ = self.stream.xDegree / 2
                            tan = np.tanh(del_)
                            wDistance = np.around(2 * tan * float(distanceFromCamera))
                            cv2.line(frame, (0, int(h / 2) + 20), (w, int(h / 2) + 20), (0, 171, 1), int(8 / DrawingFunctions.k ** DrawingFunctions.k) - 1)
                            DrawingFunctions.draw_text_on_cv_frame(frame, str(wDistance) + " m.", (30, int(h / 2) + 10),
                                                                   cv2.FONT_HERSHEY_SIMPLEX, DrawingFunctions.font_size,
                                                                   [255, 255, 255], DrawingFunctions.line_size)
                        except Exception as e:
                            print(e)

                        streams[title, "img"] = frame
                    if not need_layers:
                        streams[title, "img"] = frame
                    # capture.grab()
                    if record_required == True:
                        if writer is None:
                            print('record %d' % i)
                            fourcc = cv2.VideoWriter_fourcc(*"XVID")
                            writer = cv2.VideoWriter("/root/django/videos/output_%d.avi" % i, fourcc, 20, (w, h), True)
                        else:
                            if time.time() - t_record > 600:
                                print('time is done 60 sec.')
                                i = time.time()
                                writer.release()
                                writer = None
                                t_record = time.time()
                            else:
                                if writer != None:
                                    writer.write(frame)
                    else:
                        if writer is not None:
                            if recordIsOff == False:
                                recordIsOff = True
                                t_record = time.time()
                            else:
                                if time.time() - t_record > 900:
                                    writer.release()
                                    writer = None

                else:
                    if time.time() - last_packet > 1:
                        print("camera " + title + " reconnecting...")
                        capture.release()
                        capture = cv2.VideoCapture(self.stream.stream_in)
                        h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                        fps = int(capture.get(cv2.CAP_PROP_FPS))
                        while h == 0 and w == 0 and fps == 0:
                            capture = cv2.VideoCapture(self.stream.stream_in)
                            h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                            fps = int(capture.get(cv2.CAP_PROP_FPS))
                            time.sleep(5)
        else:
            log("Stream %s is not available" % title, "red")
        capture.release()
        streams[title, "stop_trigger"] = True
        self.stop_trigger = True
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
            Functions.update_stream_status(stream_id, title, True)
            Functions.write_status(self, StreamControl.start_thread(title))
        elif action == "stop":
            Functions.update_stream_status(stream_id, title, False)
            Functions.write_status(self, StreamControl.stop_thread(title))
        elif action == "restart":
            Functions.update_stream_status(stream_id, title, True)
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
                Functions.write_status(self, "Stream with title %s does not exist" % title)

        elif action == "update":
            json_parsed = json.loads(obj)
            stream = Stream.objects.filter(id=stream_id).last()
            if stream is not None:
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
        self.send_response(200)
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        self.set_header('Pragma', 'no-cache')
        self.set_header('Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
        self.set_header('Connection', 'close')
        self.end_headers()
        

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        ioloop = tornado.ioloop.IOLoop.current()
        title = self.get_argument("title", None)
        self.served_image_timestamp = time.time()
        log(self.request, 'cyan')
        x = 1
        while True:

            interval = 0.1 # 0.1
            # Почему это здесь, если есть метод write_image ? Зачем нужен интвервал?
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
                self.set_header("Content-type", "image/jpeg")
                self.set_header("Content-length", len(s))

#                self.write("Content-type: image/jpeg\r\n")
#                self.write("Content-length: %s\r\n\r\n" % len(s))
                self.write(s)

                #print("xeoma x = " + str(x))
                # x = x + 1
                self.served_image_timestamp = time.time()
                yield tornado.gen.Task(self.flush)
            else:
                yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)



class MJPEGHandler(tornado.web.RequestHandler):
    def get(self):
        Functions.write_header(self)
    @tornado.gen.coroutine
    def get(self):
        ioloop = tornado.ioloop.IOLoop.current()
        log(self.request, 'cyan')
        title = self.get_argument("title", None)
        title = title.split('?')[0]
        self.served_image_timestamp = time.time()
        x = 0
        interval = 0.1 # 0.1
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header("Access-Control-Allow-Methods", "*")
        self.set_header("Access-Control-Allow-Credentials", "true")
        
        self.set_header("Cache-Control",
                                "no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0")
        self.set_header("Connection", "close")
        self.set_header("Content-Type", "multipart/x-mixed-replace;boundary=--boundarydonotcross")
        self.set_header("Expires", "Mon, 3 Jan 2000 12:34:56 GMT")
        self.set_header("Pragma", "no-cache")
        while True:
            if self.served_image_timestamp + interval < time.time():
                Functions.write_image(self, title)
                x = x + 1
                log(str(x), 'cyan')
                self.served_image_timestamp = time.time()
                yield tornado.gen.Task(self.flush)
            else:
                yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)


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
