#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
from conans import AutoToolsBuildEnvironment, ConanFile, tools


class XzConan(ConanFile):
    name = "xz"
    version = "5.2.4"
    license = "Public Domain"
    url = "https://github.com/suwei-air/conan-xz"
    homepage = "https://tukaani.org/xz/"
    description = "XZ Utils is free general-purpose data compression software with a high compression ratio."
    settings = "os", "compiler", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    no_copy_source = True

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    @property
    def _xz_folder_name(self):
        return "xz-{}".format(self.version)

    @property
    def _xz_folder(self):
        return os.path.join(self.source_folder, self._xz_folder_name)

    def source(self):
        url = "https://tukaani.org/xz/{}.tar.xz".format(self._xz_folder_name)
        tools.get(url)

    def build(self):
        with tools.chdir(self._xz_folder):
            build = AutoToolsBuildEnvironment(self)
            args = [
                "--disable-xz", "--disable-xzdec", "--disable-lzmadec",
                "--disable-lzmainfo", "--disable-lzma-links",
                "--disable-scripts", "--disable-doc"
            ]
            if "fPIC" in self.options and self.options.fPIC:
                args.append("--with-pic")
            if self.options.shared:
                args.extend(["--disable-static", "--enable-shared"])
            else:
                args.extend(["--enable-static", "--disable-shared"])
            # if self.settings.build_type == "Debug":
            #     args.append("--enable-debug")
            build.configure(args=args)
            build.make()
            build.install()
