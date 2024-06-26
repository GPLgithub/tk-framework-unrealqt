# This file is based on templates provided and copyrighted by Autodesk, Inc.
# This file has been modified by Epic Games, Inc. and is subject to the license
# file included in this repository.

"""
Framework containing PySide distributions for the Unreal engine

Because Unreal does not include PySide/Qt distributions but does use its own
version of Python, we have to distribute full versions for the engine to function.
"""

import os
import platform
import re
import site
import sys

import sgtk


class UnrealQtFramework(sgtk.platform.Framework):

    ##########################################################################################
    # init and destroy

    def init_framework(self):
        """
        This framework ships with additional Python packages and tweak the Python
        paths environment to make these packages available to apps and engines.

        Something similar to what `virtualenv` does is done when this framework is
        loaded by SG TK.
        """
        self.logger.debug("%s: Initializing UnrealQtFramework..." % self)

        # Check if PySide is already available, do nothing if it is the case
        try:
            from sgtk.platform.qt import QtCore  # noqa
            self.logger.debug("Qt is already available, not activating any custom package.")
            return
        except ImportError as e:
            self.logger.debug("Qt is not available: %s, activating custom package." % e)
            pass
        # Remap the platform name to our names
        pname = self.platform_name()

        # Virtual env has different structures on Windows
        if pname == "windows":
            bin_folder = "Scripts"
        else:
            bin_folder = "bin"

        # Copied over from activate_this.py script which does not exist anymore
        # from Python 3.
        python_major = sys.version_info[0]  # 2 or 3
        python_minor = sys.version_info[1]  # 6, 7, 8, etc

        base_path = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__),
                "python",
                "vendors",
                "py%d.%d" % (python_major, python_minor),
                pname,
            )
        )
        self.logger.debug("Activating custom packages with %s" % base_path)

        if pname == "windows":
            site_path = os.path.join(base_path, "Lib", "site-packages")
        else:
            lib_folders = os.listdir(
                os.path.join(
                    base_path,
                    "lib"
                )
            )
            python_pattern = r"^python%d\.\d+$" % python_major
            for folder in lib_folders:
                if re.match(python_pattern, folder):
                    break
            else:
                raise RuntimeError(
                    "Couldn't find python libraries for Python %s from %s" % (
                        python_major,
                        lib_folders
                    )
                )
            site_path = os.path.join(
                base_path,
                "lib",
                folder,
                "site-packages"
            )

        os.environ["VIRTUAL_ENV"] = base_path
        # Split PATH, prepend our bin_folder and join back using the os path
        # separator (":" or ";")
        os.environ["PATH"] = os.pathsep.join(
            [os.path.join(base_path, bin_folder)] + os.environ.get("PATH", "").split(os.pathsep)
        )

        # Add the libraries to the host python import mechanism
        prev_length = len(sys.path)
        site.addsitedir(site_path)
        sys.path[:] = sys.path[prev_length:] + sys.path[0:prev_length]

        sys.real_prefix = sys.prefix
        sys.prefix = base_path

    def destroy_framework(self):
        self.logger.debug("%s: Destroying UnrealQtFramework..." % self)

    @classmethod
    def platform_name(cls):
        """
        Return a name for the current os that can be used
        when building os specific paths

        :returns: A name that can be used when building os specific paths.
        :raises ValueError: if the current os is not supported.
        """
        platform_names = {"Darwin": "osx", "Linux": "linux", "Windows": "windows"}
        pname = platform_names.get(platform.system())

        if not pname:
            raise ValueError("Platform %s is not supported" % platform.system())
        return pname

    @classmethod
    def bin_folder(cls, vendor=None):
        """
        Returns the bin folder for the current os
        and the given vendor where binaries can be found

        :param str vendor: An optional vendor name that will be included in the path.
        :returns: Full path to a folder.
        """
        pname = cls.platform_name()
        if vendor:
            return os.path.join(os.path.dirname(__file__), "vendors", vendor, "bin", pname)
        return os.path.join(os.path.dirname(__file__), "vendors", "bin", pname)
