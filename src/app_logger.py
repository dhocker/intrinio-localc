#
# Python logging for LO extension
# Copyright (C) 2017  Dave Hocker as TheAgency (AtHomeX10@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# See the LICENSE file for more details.
#

import logging
import logging.handlers
import os


class AppLogger:
    # All of the created loggers
    logger_list = []

    def __init__(self, logname):
        self.logger = None
        self.EnableLogging(logname)

    ########################################################################
    # Enable logging for the extension
    def EnableLogging(self, logname):
        if not logname in AppLogger.logger_list:
            # Default overrides
            logformat = '%(asctime)s, %(module)s, %(levelname)s, %(message)s'
            logdateformat = '%Y-%m-%d %H:%M:%S'

            # Logging level override
            loglevel = logging.DEBUG
            # loglevel = logging.INFO
            # loglevel = logging.WARNING
            # loglevel = logging.ERROR

            self.logger = logging.getLogger(logname)
            self.logger.setLevel(loglevel)

            formatter = logging.Formatter(logformat, datefmt=logdateformat)

            # Log to a file
            # Make logfile location OS specific
            if os.name == "posix":
                # Linux or OS X
                file_path = "{0}/libreoffice/intrinio/".format(os.environ["HOME"])
            elif os.name == "nt":
                # Windows
                file_path = "{0}\\libreoffice\\intrinio\\".format(os.environ["LOCALAPPDATA"])
            logfile = file_path + logname + ".log"

            fh = logging.handlers.TimedRotatingFileHandler(logfile, when='midnight', backupCount=3)
            fh.setLevel(loglevel)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            self.logger.debug("%s logging to file: %s", logname, logfile)

            # Note that this logname has been defined
            AppLogger.logger_list.append(logname)
        else:
            # Use the logger that has been previously defined
            self.logger = logging.getLogger(logname)

    def getAppLogger(self):
        """
        Return an instance of the default logger for this app.
        :return: logger instance
        """
        return self.logger

    # Controlled logging shutdown
    def Shutdown(self):
        self.getAppLogger().debug("Logging shutdown")
        logging.shutdown()
