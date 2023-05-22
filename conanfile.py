import os

from conan.tools.files import get
from conans import ConanFile, AutoToolsBuildEnvironment


class LibNodeConan(ConanFile):
    name = "node"
    version = "18.16.0"
    # version = "14.16.1"

    # Optional metadata
    license = "MIT"
    homepage = "https://github.com/nodejs/node"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Node.js JavaScript runtime"
    settings = "os", "compiler", "build_type", "arch"

    # Binary configuration
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {
        "shared": False,
        "fPIC": True,
        "icu:shared": True,
    }

    def requirements(self):
        if self.settings.os != "Windows":
            self.requires("ninja/1.11.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        if self.settings.os == "Windows":
            args = [
                "nonpm",
                "nocorepack",
                "no-cctest",
                "without-intl",
                "no-shared-roheap",
                "no-NODE-OPTIONS",
            ]

            if self.settings.build_type == "Debug":
                args.append("debug")
            else:
                args.append("release")
            if self.options.shared:
                args.append("dll")
            else:
                args.append("static")
            self.run("vcbuild.bat {0}".format(" ".join(args)))
        else:
            autotools = AutoToolsBuildEnvironment(self)

            cflags = []
            args = [
                "--without-npm",
                "--without-intl",
                "--without-corepack",
                "--without-node-options",
                "--without-ssl",
                "--without-node-snapshot",
                "--ninja"
            ]

            if self.options.fPIC:
                cflags.append("-fPIC")
            if self.options.shared:
                args.append("--shared")

            cflags.append("-fvisibility=default")

            cflags_str = " ".join(cflags)

            build_vars = {
                "CFLAGS": cflags_str,
                "CXXFLAGS": cflags_str,
            }

            autotools.configure(args=args, vars=build_vars)
            autotools.make(vars=build_vars)

    def package(self):
        if self.settings.os == "Windows":
            self.copy("*.h", dst="include", src="deps/v8/include/")
            self.copy("*.h", dst="include/node", src="src")
            self.copy("libnode.dll", dst="bin", src="out/{}".format(self.settings.build_type), keep_path=False)
            self.copy("libnode.lib", dst="lib", src="out/{}".format(self.settings.build_type), keep_path=False)
            self.copy("v8_libplatform.lib", dst="lib", src="out/{}/lib".format(self.settings.build_type),
                      keep_path=False)
        else:
            self.copy("*.h", dst="include/node", src="src")
            self.copy("*.h", dst="include", src="deps/v8/include/")
            self.copy("libnode.lib", src="out/{}".format(self.settings.build_type), dst="lib",
                      keep_path=False
                      )
            self.copy(
                "libnode.a", src="out/{}".format(self.settings.build_type), dst="lib", keep_path=False
            )

            if self.options.shared:
                self.copy(
                    "libnode.so*",
                    src="out/{}".format(self.settings.build_type),
                    dst="lib",
                    keep_path=False,
                    symlinks=True,
                )
                self.copy(
                    "*.dylib",
                    src="out/{}".format(self.settings.build_type),
                    dst="lib",
                    keep_path=False,
                    symlinks=True,
                )

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["node", "v8_libplatform"]
        else:
            self.cpp_info.libs = ["node"]
