#
# intrinio_lib - Reusable classes and functions for accessing Intrinio
# Copyright (C) 2017  Dave Hocker (email: AtHomeX10@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the LICENSE file for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program (the LICENSE file).  If not, see <http://www.gnu.org/licenses/>.
#

import urllib.request
import urllib.parse
import urllib.error
import json
import os
import ssl
from app_logger import AppLogger

# Logger init
app_logger = AppLogger("intrinio-extension")
logger = app_logger.getAppLogger()


class QConfiguration:
    """
    Encapsulates Intrinio credentials
    """
    auth_user = ""
    auth_passwd = ""
    # Base URL for Intrinio services
    base_url = "https://api.intrinio.com"
    macOS = False
    full_file_path = ""
    cacerts = ""

    @classmethod
    def load(cls):
        """
        Load credentials from configuration file. The location of the intrinio.conf
        file is OS dependent. The permissions of the intrinio.conf file should allow
        access ONLY by the user.
        :return: None
        """
        file_name = "intrinio.conf"
        if os.name == "posix":
            # Linux or OS X
            file_path = "{0}/libreoffice/intrinio/".format(os.environ["HOME"])
            cls.macOS = (os.uname()[0] == "Darwin")
        elif os.name == "nt":
            # Windows
            file_path = "{0}\\libreoffice\\intrinio\\".format(os.environ["APPDATALOCAL"])
        cls.full_file_path = file_path + file_name

        # Read credentials
        try:
            cf = open(QConfiguration.full_file_path, "r")
            cfj = json.loads(cf.read())
            cls.auth_user = cfj["user"]
            cls.auth_passwd = cfj["password"]
            if "certifi" in cfj:
                cls.cacerts = cfj["certifi"]
            cf.close()
        except FileNotFoundError as ex:
            logger.error("%s was not found", cls.full_file_path)
        except Exception as ex:
            logger.error("An exception occurred while attempting to load intrinio.conf")
            logger.error(str(ex))

    @classmethod
    def get_masked_user(cls):
        return cls.auth_user[:int(len(cls.auth_user) / 2)] + ("*" * int(len(cls.auth_user) / 2))

    @classmethod
    def is_configured(cls):
        """
        Intrinio is configured if there is a user and password in the intrinio.conf file.
        :return:
        """
        if cls.macOS:
            return QConfiguration.auth_user and QConfiguration.auth_passwd and QConfiguration.cacerts
        return QConfiguration.auth_user and QConfiguration.auth_passwd

# Set up configuration with user credentials
QConfiguration.load()

class IntrinioBase:

    @staticmethod
    def setup_authorization(url_string):
        """
        Set up basic authorization for the given URL.
        :param url_string:
        :return: None
        """
        passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url_string, QConfiguration.auth_user, QConfiguration.auth_passwd)
        authhandler = urllib.request.HTTPBasicAuthHandler(passman)
        ssl_ctx = ssl.create_default_context(cafile=QConfiguration.cacerts)
        httpshandler = urllib.request.HTTPSHandler(context=ssl_ctx)
        opener = urllib.request.build_opener(httpshandler, authhandler)
        urllib.request.install_opener(opener)

    @staticmethod
    def get_usage(access_code):
        """
        Get Intrinio usage stats for the given access_code
        :param access_code:
        :return: Usage stats in a dict
        """
        template_url = "{0}/usage/current?access_code={1}"
        url_string = template_url.format(QConfiguration.base_url, access_code)
        res = IntrinioBase.exec_request(url_string)
        return res

    @staticmethod
    def get_excel_version():
        """
        Get Excel version info. Really not useful for LOCalc, but included as an exercise.
        :return: Version info in a dict
        """
        template_url = "{0}/excel"
        url_string = template_url.format(QConfiguration.base_url)
        res = IntrinioBase.exec_request(url_string)
        return res

    @staticmethod
    def exec_request(url_string):
        """
         Submit https request to Intrinio
        :param url_string:
        :return: JSON decoded dict containing results of https GET.
        The status_code key is added to return the HTTPS status code.
        """
        # print(url_string)
        IntrinioBase.setup_authorization(url_string)
        try:
            logger.debug("Calling Intrinio: %s", url_string)
            response = urllib.request.urlopen(url_string)
            status_code = response.getcode()
            res = response.read()
            res = str(res, "utf-8")
        except urllib.error.HTTPError as ex:
            logger.error(ex.msg)
            logger.error(str(ex))
            return {"status_code":ex.code}

        j = json.loads(res)
        j["status_code"] = status_code
        return j


#
# Intrinio login dialog
# Adapted from https://forum.openoffice.org/en/forum/viewtopic.php?f=45&t=56397#p248794
#


try:
    import uno
    logger.debug("Attempt to import uno succeeded")
    # logger.debug("sys.path = %s", sys.path)
except Exception as ex:
    logger.error("Attempt to import uno failed %s", str(ex))
try:
    # https://www.openoffice.org/api/docs/common/ref/com/sun/star/awt/PosSize.html
    from com.sun.star.awt.PosSize import POSSIZE # flags the x- and y-coordinate, width and height
    logger.debug("Attempt to import com.sun.star.awt.PosSize succeeded")
except Exception as ex:
    logger.error("Attempt to import com.sun.star.awt.PosSize failed %s", str(ex))


def _add_awt_model(dlg_model, srv, ctl_name, prop_list):
    '''
    Helper function for building dialog
    Insert UnoControl<srv>Model into given DialogControlModel oDM by given sName and properties dProps
    '''
    ctl_model = dlg_model.createInstance("com.sun.star.awt.UnoControl" + srv + "Model")
    while prop_list:
        prp = prop_list.popitem()
        uno.invoke(ctl_model,"setPropertyValue",(prp[0],prp[1]))
        #works with awt.UnoControlDialogElement only:
        ctl_model.Name = ctl_name
    dlg_model.insertByName(ctl_name, ctl_model)


def intrinio_login():
    """
    Ask user for Intrinio login credentials
    :return: If successful, returns username and password as a tuple (something truthy)
    If canceled, returns False.
    """
    # Reference: https://www.openoffice.org/api/docs/common/ref/com/sun/star/awt/module-ix.html
    global logger

    ctx = uno.getComponentContext()
    smgr = ctx.ServiceManager
    dlg_model = smgr.createInstance("com.sun.star.awt.UnoControlDialogModel")
    dlg_model.Title = 'Intrinio Access Keys'
    _add_awt_model(dlg_model, 'FixedText', 'lblName', {
        'Label': 'User Name',
    }
                   )
    _add_awt_model(dlg_model, 'Edit', 'txtName', {})
    _add_awt_model(dlg_model, 'FixedText', 'lblPWD', {
        'Label': 'Password',
    }
                   )
    _add_awt_model(dlg_model, 'Edit', 'txtPWD', {
        'EchoChar': 42,
    }
                   )
    _add_awt_model(dlg_model, 'Button', 'btnOK', {
        'Label': 'Save',
        'DefaultButton': True,
        'PushButtonType': 1,
    }
                   )
    _add_awt_model(dlg_model, 'Button', 'btnCancel', {
        'Label': 'Cancel',
        'PushButtonType': 2,
    }
                   )

    lmargin = 10  # left margin
    rmargin = 10  # right margin
    tmargin = 10  # top margin
    bmargin = 10  # bottom margin
    cheight = 25  # control height
    pad = 5  # top/bottom padding where needed
    theight = cheight + pad  # total height of a control

    # Poor man's grid
    # layout "control-name", [x, y, w, h]
    layout = {
        "lblName": [lmargin, tmargin, 100, cheight],
        "txtName": [lmargin + 100, tmargin, 250, cheight],
        "lblPWD": [lmargin, tmargin + (theight * 1), 100, cheight],
        "txtPWD": [lmargin + 100, tmargin + (theight * 1), 250, cheight],
        "btnOK": [lmargin + 100, tmargin + (theight * 2), 100, cheight],
        "btnCancel": [lmargin + 200, tmargin + (theight * 2), 100, cheight]
    }

    dialog = smgr.createInstance("com.sun.star.awt.UnoControlDialog")
    dialog.setModel(dlg_model)
    name_ctl = dialog.getControl('txtName')
    pass_ctl = dialog.getControl('txtPWD')

    # Apply layout to controls. Must be done within the dialog.
    for name, d in layout.items():
        ctl = dialog.getControl(name)
        ctl.setPosSize(d[0], d[1], d[2], d[3], POSSIZE)

    dialog.setPosSize(300, 300, lmargin + rmargin + 100 + 250, tmargin + bmargin + (theight * 3), POSSIZE)
    dialog.setVisible(True)

    # Run the dialog. Returns the value of the PushButtonType.
    # 1 = save
    # 2 = cancel
    button_id = dialog.execute()
    logger.debug("intrinio login dialog returned: %s", x)
    if button_id == 1:
        return (name_ctl.getText(), pass_ctl.getText())
    else:
        return False
