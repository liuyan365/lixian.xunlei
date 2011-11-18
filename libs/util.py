# -*- encoding: utf-8 -*-
# author: binux<17175297.hk@gmail.com>

import logging
import thread
import tornado
from multiprocessing import Pipe

units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def format_size(request, size):
    i = 0
    while size > 1024:
        size /= 1024
        i += 1
    return "%d%s" % (size, units[i])

d_status = {
        "finished": u"完成",
        "downloading": u"下载中",
        "waiting": u"队列中",
        "failed": u"下载失败",
        "pause": u"暂停中",
}
def format_download_status(status):
    return d_status.get(status, u"未知状态")

def determin_url_type(url):
    url_lower = url.lower()
    if url_lower.endswith(".torrent"):
        return "bt"
    elif url_lower.startswith("ed2k"):
        return "ed2k"
    elif url_lower.startswith("thunder"):
        return "thunder"
    elif url_lower.startswith("magnet"):
        return "magnet"
    else:
        return "normal"

ui_methods = {
        "format_size": format_size,
        "format_status": format_download_status,
}

class AsyncProcessMixin(object):
    def call_subprocess(self, func, callback=None, args=[], kwargs={}):
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.pipe, child_conn = Pipe()

        def wrap(func, pipe, args, kwargs):
            try:
                pipe.send(func(*args, **kwargs))
            except Exception, e:
                pipe.send(e)
        
        self.ioloop.add_handler(self.pipe.fileno(),
                  self.async_callback(self.on_pipe_result, callback),
                  self.ioloop.READ)
        thread.start_new_thread(wrap, (func, child_conn, args, kwargs))

    def on_pipe_result(self, callback, fd, result):
        try:
            ret = self.pipe.recv()
            if isinstance(ret, Exception):
                raise ret

            if callback:
                callback(ret)
        finally:
            self.ioloop.remove_handler(fd)