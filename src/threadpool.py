# Thread pool to be used with Tornado.
# from https://github.com/ovidiucp/pymysql-benchmarks
# see https://groups.google.com/forum/#!msg/python-tornado/SmNsJwb4x0E/S2Z81Asz5CwJ
#
# Author: Ovidiu Predescu
# Date: August 2011
#
# Rewritten by: makeroo
# Date: June 2014


#import sys
#import _thread
from threading import Thread, local
from queue import Queue, Empty
from functools import partial
import tornado.ioloop
#import time

class ThreadPool (object):
    """Creates a thread pool containing `num_threads' worker threads.

    The caller can execute a task in a worker thread by invoking
    add_task(). The `func' argument will be executed by one of the
    worker threads as soon as one becomes available. If `func' needs
    to take any arguments, wrap the function using functools.partial.

    The caller has the option of specifying a callback to be invoked
    on the main thread's IOLoop instance. In a callback is specified
    it is passed as argument the return value of `func'.

    Each thread receive a global context and can use a local storage.
    Function called by thread receives them by keyword argument:
    global_data and local_data respectively.

    Example prototype:

    def func (..., global_data=None, local_data=None):
        ...
        return some-result

    To stop the worker threads in the thread pool use the stop()
    method.

    The queue_timeout parameter sets the time queue.get() waits for an
    object to appear in the queue. The default is 1 second, which is
    low enough for interactive usage. It should be lowered to maybe
    0.001 (1ms) to make unittests run fast, and increased when you
    expect the thread pool to be rarely stopped (like in a production
    environment).
    """

    def __init__ (self,
                  thread_global_data=None,
                  thread_quit_hook=None,
                  num_threads=10,
                  queue_timeout=1,
                  ioloop=tornado.ioloop.IOLoop.instance()):
        self._ioloop = ioloop
        self._num_threads = num_threads
        self._queue = Queue()
        self._queue_timeout = queue_timeout
        self._threads = []
        self._running = True
        for i in range(num_threads):
            t = WorkerThread(self, thread_global_data, thread_quit_hook)
            t.name = 'Worker Thread %s' % i
            t.daemon = True
            t.start()
            self._threads.append(t)

    def add_task (self, func, callback=None):
        """Add a function to be invoked in a worker thread."""
        self._queue.put((func, callback))

    def stop (self):
        self._running = False
        for t in self._threads:
            t.join()

class WorkerThread (Thread):
    def __init__ (self, pool, thread_global_data, thread_quit_hook):
        super(WorkerThread, self).__init__()
        self._pool = pool
        self._thread_global_data = thread_global_data
        self._thread_quit_hook = thread_quit_hook

    def run (self):
        queue = self._pool._queue
        queue_timeout = self._pool._queue_timeout
        gdata = self._thread_global_data
        ldata = local()
        try:
            while self._pool._running:
                try:
                    (func, callback) = queue.get(True, queue_timeout)
                    result = func(global_data=gdata, local_data=ldata)
                    if callback:
                        self._pool._ioloop.add_callback(partial(callback, result))
                except Empty:
                    pass
        finally:
            if self._thread_quit_hook:
                self._thread_quit_hook(gdata, ldata)
