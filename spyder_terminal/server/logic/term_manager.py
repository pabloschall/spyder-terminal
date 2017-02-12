# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import sys
import time
import pexpect
import hashlib
import tornado.web
import tornado.gen
import tornado.ioloop
import pexpect.popen_spawn as pspawn

WINDOWS = 'nt'

class TermReader(object):
    def __init__(self, tty, socket):
        self.tty = tty
        self.socket = socket
        self.p_callback = tornado.ioloop.PeriodicCallback(self.consume_lines,
                                                          callback_time=10)
        self.p_callback.start()

    @tornado.gen.coroutine
    def consume_lines(self):
        # print("Reading")
        # while self.tty.isalive():
        try:
            _in = self.tty.read_nonblocking(timeout=0, size=1000)
            self.socket.notify(_in)
        except:
            pass


class TermManager(object):
    """Wrapper around pexpect to execute local commands."""
    def __init__(self):
        self.os = os.name
        if self.os == WINDOWS:
            self.cmd = 'cmd'
            self.pty_fork = pspawn.PopenSpawn
        else:
            self.cmd = '/usr/bin/env bash'
            self.pty_fork = pexpect.spawnu
        self.sockets = {}
        self.consoles = {}

    @tornado.gen.coroutine
    def create_term(self, rows, cols):
        pid = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()[0:6]
        tty = self.pty_fork(self.cmd)
        self.consoles[pid] = {'tty':tty, 'read':None}
        self.resize_term(pid, rows, cols)
        # self.sockets[pid] = socket
        raise tornado.gen.Return(pid)

    @tornado.gen.coroutine
    def start_term(self, pid, socket):
        term = self.consoles[pid]
        self.sockets[pid] = socket
        term['tty'].expect('')
        # self.sockets[pid].notify(term['tty'].before)
        term['read'] = TermReader(term['tty'], socket)
        # a = yield term['read'].consume_lines()

    @tornado.gen.coroutine
    def stop_term(self, pid):
        term = self.consoles[pid]
        term['tty'].close()
        del self.consoles[pid]
        del self.sockets[pid]

    @tornado.gen.coroutine
    def execute(self, pid, cmd):
        term = self.consoles[pid]['tty']
        term.send(cmd)

    @tornado.gen.coroutine
    def resize_term(self, pid, rows, cols):
        term = self.consoles[pid]['tty']
        term.setwinsize(rows, cols)