import tornado.escape
import tornado.gen
import cv2
import io
import tornado.ioloop
import tornado.web
import time
import os
import tornado
from PIL import Image
from termcolor import colored
from PIL.JpegImagePlugin import JpegImageFile
# file_list = os.listdir("img")
counter = 0





class MJPEGHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        ioloop = tornado.ioloop.IOLoop.current()
        capture = cv2.VideoCapture("rtsp://172.19.1.10:554/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp?real_stream")
        h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(capture.get(cv2.CAP_PROP_FPS))
        print("W=%d, H=%d, FPS=%d " % (w, h, fps))
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


        self.served_image_timestamp = time.time()
        # my_boundary = "--boundarydonotcross\n"
        if capture.isOpened():
            while True:
                ret, frame = capture.read()
                interval = 1.0
                if self.served_image_timestamp + interval < time.time():
                    o = io.BytesIO()
                    img = Image.fromarray(frame)
                    o.seek(0)
                    img.save(o, format="JPEG")
                    s = o.getvalue()
                    print(len(s))
                    self.write("--boundarydonotcross\n")
                    self.write("Content-type: image/jpeg\r\n")
                    self.write("Content-length: %s\r\n\r\n" % len(s))
                    self.write(s)
                    self.served_image_timestamp = time.time()
                    yield tornado.gen.Task(self.flush)
                else:
                    yield tornado.gen.Task(ioloop.add_timeout, ioloop.time() + interval)


application = tornado.web.Application([
    (r"/", MJPEGHandler),
])


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()