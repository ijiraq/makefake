"""VO File helper class"""
import shutil
from datetime import datetime
from logging import handlers
from vos import Client
from cadcutils.exceptions import NotFoundException
import logging
import numpy
import os
import re
import subprocess
import time
import sys
import six
import tempfile


def exec_prog(args):
    """Run a subprocess, check for .OK and raise error if does not exist.

    args:  list of arguments, for value is the command to execute.
    """

    program_name = args[0]
    logging.info(" ".join(args))
    output = subprocess.check_output(args, stderr=subprocess.STDOUT)
    if not os.access(program_name+".OK", os.F_OK):
        logging.error("No {}.OK file?".format(program_name))
        raise subprocess.CalledProcessError(-1, ' '.join(args), output)
    os.unlink(program_name+".OK")
    if os.access(program_name+".FAILED", os.F_OK):
        os.unlink(program_name+".FAILED")
    return output


class VOFileHandler(handlers.BufferingHandler):
    """
    A handler class that writes formatted logging records to VOSpace files.
    """
    def __init__(self, filename, vos_client=None):
        self.filename = filename
        self._client = vos_client
        self._stream = None
        super(VOFileHandler, self).__init__(1024*1024)

    @property
    def is_vospace(self) -> bool:
        """
        Determine if filename indicates this is a VOSpace file.
        """
        return self.filename.startswith('vos:') or self.filename.startswith('arc:')

    @property
    def stream(self) -> tempfile.NamedTemporaryFile:
        """
        The stream to write the log content too.

        First pull the existing content of this log file from existing location and then append current content.

        We either pull the file from 'vos' or 'arc' or the local filesystem.
        @return:
        """
        if self._stream is None:
            self._stream = tempfile.NamedTemporaryFile(delete=False)
            if self.is_vospace:
                try:
                    self._stream.write(self.client.open(self.filename, view='data').read())
                except NotFoundException:
                    pass
            elif os.access(self.filename, os.R_OK):
                self._stream.write(open(self.filname, 'r').read())
        return self._stream

    @property
    def client(self) -> Client:
        """
        Send back the client we were sent, or construct a default one.

        """
        if self._client is not None:
            return self._client
        self._client = Client()
        return self._client

    def close(self):
        """
        Closes the logging stream and copies contents of log to end of 'self.filename'.
        """

        if self.stream is None:
            return

        self.flush()
        self.stream.flush()
        _name = self.stream.name
        self.stream.close()

        if self.is_vospace:
            self.client.copy(_name, self.filename)
        else:
            shutil.copy(_name, self.filename)

    def flush(self):
        for record in self.buffer:
            self.stream.write(bytes("{}\n".format(self.format(record)), 'utf-8'))
        self.buffer = []
