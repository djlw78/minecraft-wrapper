# -*- coding: utf-8 -*-

import json
import os
import logging
from logging.config import dictConfig

from utils.helpers import mkdir_p, use_style

DEFAULT_CONFIG = dict({
    "wrapperversion": 1.1,
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "()": "utils.log.ColorFormatter",
            "format": "[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s",
            "datefmt": "%H:%M:%S"
        },
        "file": {
            "format": "[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "trace": {
            "format": "[%(asctime)s] [%(name)s/%(levelname)s] [THREAD:%(threadName)s]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "filters": [],
            "stream": "ext://sys.stdout"
        },
        "wrapper_file_handler": {
            "class": "utils.log.WrapperHandler",
            "level": "INFO",
            "formatter": "file",
            "filters": [],
            "filename": "logs/wrapper/wrapper.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
        "error_file_handler": {
            "class": "utils.log.WrapperHandler",
            "level": "ERROR",
            "formatter": "file",
            "filters": [],
            "filename": "logs/wrapper/wrapper.errors.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
        "trace_file_handler": {
            "class": "utils.log.WrapperHandler",
            "level": "ERROR",
            "formatter": "trace",
            "filters": [],
            "filename": "logs/wrapper/wrapper.trace.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        }
    },
    "root": {
        "level": "NOTSET",
        "handlers": ["console", "wrapper_file_handler", "error_file_handler", "trace_file_handler"]
    }
})


def configure_logger():
    setcustomlevels()
    loadconfig()

    logging.getLogger()


def setcustomlevels():
    # Create a TRACE level
    # We should probably not do this, but for wrappers use case this is non-impacting.
    # See: https://docs.python.org/2/howto/logging.html#custom-levels
    logging.TRACE = 5  # lower than DEBUG
    logging.addLevelName(logging.TRACE, "TRACE")
    logging.Logger.trace = lambda inst, msg, *args, **kwargs: inst.log(logging.TRACE, msg, *args, **kwargs)


def loadconfig(configfile="logging.json"):
    dictConfig(DEFAULT_CONFIG)  # Load default config
    try:
        if os.path.isfile(configfile):
            with open(configfile, "r") as f:
                conf = json.load(f)
            # Use newer logging configuration, if the one on disk is too old

            if "wrapperversion" not in conf or (conf["wrapperversion"] < DEFAULT_CONFIG["wrapperversion"]):
                with open(configfile, "w") as f:
                    f.write(json.dumps(DEFAULT_CONFIG, indent=4, separators=(',', ': ')))
                logging.warning("Logging configuration updated (%s) -- creating new logging configuration", configfile)
            else:
                dictConfig(conf)
                logging.info("Logging configuration file (%s) located and loaded, logging configuration set!",
                             configfile)
        else:
            with open(configfile, "w") as f:
                f.write(json.dumps(DEFAULT_CONFIG, indent=4, separators=(',', ': ')))
            logging.warning("Unable to locate %s -- Creating default logging configuration", configfile)
    except Exception as e:
        logging.exception("Unable to load or create %s! (%s)", configfile, e)


class ColorFormatter(logging.Formatter):
    """
    This custom formatter will format console color/option (bold, italic, etc) output based on logging level
    """
    def __init__(self, *args, **kwargs):
        super(ColorFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        args = record.args
        msg = record.msg

        if os.name in ("posix", "mac"):  # Only style on *nix since windows doesn't support ANSI
            if record.levelno == logging.INFO:
                info_style = use_style(foreground="green")
                msg = info_style(msg)
            elif record.levelno == logging.DEBUG:
                debug_style = use_style(foreground="cyan")
                msg = debug_style(msg)
            elif record.levelno == logging.WARNING:
                warn_style = use_style(foreground="yellow", options=("bold",))
                msg = warn_style(msg)
            elif record.levelno == logging.ERROR:
                error_style = use_style(foreground="red", options=("bold",))
                msg = error_style(msg)
            elif record.levelno == logging.CRITICAL:
                crit_style = use_style(foreground="black", background="red", options=("bold",))
                msg = crit_style(msg)
            elif record.levelno == logging.TRACE:
                trace_style = use_style(foreground="white", background="black", options=("italic",))
                msg = trace_style(msg)

        record.msg = msg

        return super(ColorFormatter, self).format(record)


class WrapperHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=0):
        mkdir_p(os.path.dirname(filename))
        super(WrapperHandler, self).__init__(filename, mode, maxBytes, backupCount, encoding, delay)
