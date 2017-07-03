#
# Package extension files into an .oxt file
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
# References
# https://wiki.openoffice.org/wiki/Calc/Add-In/Python_How-To
# http://www.biochemfusion.com/doc/Calc_addin_howto.html
# https://github.com/madsailor/SMF-Extension
#

import os
import subprocess
import shutil
from xcu_file import XCUFile

# Set up environment vars
os.environ["PATH"] = os.environ["PATH"] + ":/usr/lib/ure/bin/"
os.environ["PATH"] = os.environ["PATH"] + ":/Users/dhocker/LibreOffice5.3_SDK/bin"
os.environ["DYLD_LIBRARY_PATH"] = os.environ["OO_SDK_URE_LIB_DIR"]
#subprocess.call("env")
#print (os.environ["DYLD_LIBRARY_PATH"])

# Create required build folders
if not os.path.exists("build"):
    print ("Creating build folder")
    os.mkdir("build")
if not os.path.exists("build/META-INF"):
    print ("Creating build/META-INF folder")
    os.mkdir("build/META-INF")

# Compile idl
subprocess.call(["idlc", "idl/xintrinio.idl"])
subprocess.call(["regmerge", "-v", "build/xintrinio.rdb", "UCR", "idl/xintrinio.urd"])
os.remove("idl/xintrinio.urd")

# Copy all required files to build folder
print ("Copying files to build folder")
shutil.copy("src/manifest.xml", "build/META-INF/")
shutil.copy("src/description-en-US.txt", "build/")
shutil.copy("src/description.xml", "build/")
shutil.copy("src/intrinio_impl.py", "build/")
shutil.copy("src/app_logger.py", "build/")
# shutil.copy("src/intrinio_lib.py", "build/")
# shutil.copy("src/intrinio_stats.py", "build/")

# Generate the XCU file
print ("Generating intrinio.xcu")
xcu = XCUFile("com.intrinio.fintech.localc.python.IntrinioImpl", "XIntrinio")
xcu.add_function("getIntrinioUsage", "Get Intrinio usage satistics", [('a', 'The access code ID.'), ('b', 'The statistic key name.')])
xcu.generate("build/intrinio.xcu")

# Zip contents of build folder and rename it to .oxt
print ("Zipping build files into .oxt file")
os.chdir("build/")
for f in os.listdir("./"):
    if os.path.isfile(f) or os.path.isdir(f):
        subprocess.call(["zip", "-r", "intrinio.zip", f])
os.chdir("..")
shutil.move("build/intrinio.zip", "intrinio.oxt")
print ("Extension file intrinio.oxt created")

print ("Build complete")
