import signal
from django.core.management.base import BaseCommand
from control_pane.lib.VideoHandler.process_stream import run_server,StreamControl
from control_pane.models import Stream

START_THREADS_ON_RUN = False

class Command(BaseCommand):
    args = '[port_number]'
    help = 'Starts the Tornado application for message handling.'

    def sig_handler(self, sig, frame):
        """Catch signal and init callback"""

    def shutdown(self):
        """Stop server and add callback to stop i/o loop"""
        self.http_server.stop()

    def handle(self, *args, **options):
        StreamControl.init_threads()
        streams = Stream.objects.filter(status = True)
        for stream in streams:
            print(stream.title)
            StreamControl.start_thread(stream.title)

        run_server()
        print('Finish')
        # Init signals handler
        signal.signal(signal.SIGTERM, self.sig_handler)

        # This will also catch KeyboardInterrupt exception
        signal(signal.SIGINT, self.sig_handler)
