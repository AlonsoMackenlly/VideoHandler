import time
from datetime import datetime
log_filename = "../../log.txt"
def log(text, importance = "INFO"):
    row = "[%s] %s - %s"%(importance, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), text)
    print(row)
    log_file = open(log_filename, "a")
    log_file.write(row+"\n")
    log_file.flush()