#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
from conans import AutoToolsBuildEnvironment, ConanFile, MSBuild, tools


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

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    @property
    def _xz_folder_name(self):
        return "xz-{}".format(self.version)

    @property
    def _xz_folder(self):
        return os.path.join(self.source_folder, self._xz_folder_name)

    @property
    def _xz_vs_folder(self):
        compiler_version = int(self.settings.compiler.version.value)
        vs_folder = "vs2017" if compiler_version >= 15 else "vs2013"
        return os.path.join(self._xz_folder, "windows", vs_folder)

    @property
    def _vs_arch_map(self):
        return {"x86": "Win32", "x86_64": "x64"}

    @property
    def _vs_target(self):
        return "liblzma_dll" if self.options.shared else "liblzma"

    @property
    def _vs_build_type(self):
        # return "Debug" if self.settings.build_type == "Debug" else "Release"
        return "Release"

    def source(self):
        url = "https://tukaani.org/xz/{}.tar.xz".format(self._xz_folder_name)
        tools.get(url)
        # don't specify Windows SDK version
        vs_folder = os.path.join(self._xz_folder, "windows", "vs2017")
        tools.replace_in_file(
            os.path.join(vs_folder, "liblzma.vcxproj"),
            "<WindowsTargetPlatformVersion>10.0.15063.0</WindowsTargetPlatformVersion>",
            "")
        tools.replace_in_file(
            os.path.join(vs_folder, "liblzma_dll.vcxproj"),
            "<WindowsTargetPlatformVersion>10.0.15063.0</WindowsTargetPlatformVersion>",
            "")

    def build(self):
        if self.settings.compiler == "Visual Studio":
            build = MSBuild(self)
            build.build(
                os.path.join(self._xz_vs_folder, "xz_win.sln"),
                targets=[self._vs_target],
                upgrade_project=False,
                build_type=self._vs_build_type,
                platforms=self._vs_arch_map)
        else:
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
                host = None
                vars = None
                if self.settings.os == "Android":
                    toolchain = os.path.join(
                        os.environ["ANDROID_HOME"], "ndk-bundle", "toolchains",
                        "llvm", "prebuilt", "linux-x86_64", "bin")
                    if self.settings.arch == "armv7":
                        host = "armv7a-linux-androideabi"
                        cmd_prefix = "arm-linux-androideabi"
                    vars = {
                        "AR":
                        os.path.join(toolchain, cmd_prefix + "-ar"),
                        "AS":
                        os.path.join(toolchain, cmd_prefix + "-as"),
                        "CC":
                        os.path.join(
                            toolchain, "{}{}-clang".format(
                                host, self.settings.os.api_level)),
                        "CXX":
                        os.path.join(
                            toolchain, "{}{}-clang++".format(
                                host, self.settings.os.api_level)),
                        "LD":
                        os.path.join(toolchain, cmd_prefix + "-ld"),
                        "RANLIB":
                        os.path.join(toolchain, cmd_prefix + "-ranlib"),
                        "STRIP":
                        os.path.join(toolchain, cmd_prefix + "-strip"),
                    }
                elif self.settings.os == "iOS":
                    iphoneos = tools.XCRun(self.settings, sdk="iphoneos")
                    flags = "-arch armv7 -arch armv7s -arch arm64 -isysroot " + iphoneos.sdk_path
                    vars = {
                        "AR": iphoneos.ar,
                        "CC": iphoneos.cc,
                        "CXX": iphoneos.cxx,
                        "LD": iphoneos.find("ld"),
                        "CFLAGS": flags,
                        "CXXFLAGS": flags,
                    }
                build.configure(args=args, host=host, vars=vars)
                build.make()
                build.install()

    def package(self):
        if self.settings.compiler == "Visual Studio":
            header_dir = os.path.join(self._xz_folder, "src", "liblzma", "api")
            self.copy(
                pattern="*.h", dst="include", src=header_dir, keep_path=True)
            arch = self._vs_arch_map.get(str(self.settings.arch))
            bin_dir = os.path.join(self._xz_vs_folder, str(
                self._vs_build_type), arch, self._vs_target)
            self.copy(pattern="*.lib", dst="lib", src=bin_dir, keep_path=False)
            self.copy(pattern="*.pdb", dst="bin", src=bin_dir, keep_path=False)
            if self.options.shared:
                self.copy(
                    pattern="*.dll", dst="bin", src=bin_dir, keep_path=False)
