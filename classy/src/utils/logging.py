"""
Use this module to setup logging of executed scripts.

Allow scripts to have results logged to a VOSpace annotation associated to a file relevant to the exectued script.
"""
import logging

def log_filename(prefix, task, version, ccd):
    return "{}{}_{}{}{}".format(prefix, task, version, ccd, TEXT_EXT)

def log_location(expnum, ccd):
    return os.path.dirname(Artifact(Observation(expnum), ccd=ccd).uri)


class LoggingManager:
    """
    Manage the process of starting scripts and logging the results to VOSpace anotation
    """

    def __init__(self, task:str, prefix:str, expnum:str, ccd:int, version:str, dry_run:bool = False):
        self.logging = logging.getLogger('')
        self.log_format = logging.Formatter('%(asctime)s - %(module)s.%(funcName)s %(lineno)d: %(message)s')
        self.filename = log_filename(prefix, task, ccd=ccd, version=version)
        self.location = log_location(expnum, ccd)
        self.dry_run = dry_run

    def __enter__(self):
        if not self.dry_run:
            self.vo_handler = util.VOFileHandler("/".join([self.location, self.filename]))
            self.vo_handler.setFormatter(self.log_format)
            self.logging.addHandler(self.vo_handler)
        self.file_handler = logging.FileHandler(filename=self.filename)
        self.file_handler.setFormatter(self.log_format)
        self.logging.addHandler(self.file_handler)
        return self

    def __exit__(self, *args):
        if not self.dry_run:
            self.logging.removeHandler(self.vo_handler)
            self.vo_handler.close()
            del self.vo_handler
        self.logging.removeHandler(self.file_handler)
        self.file_handler.close()
        del self.file_handler

