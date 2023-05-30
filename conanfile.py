import os

from conan.tools.files import get, rm, export_conandata_patches, apply_conandata_patches
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
        "fPIC": True
    }

    def requirements(self):
        if self.settings.os != "Windows":
            self.requires("ninja/1.11.1")

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        if self.settings.os == "Windows":
            apply_conandata_patches(self)
            args = [
                "nonpm",
                "nocorepack",
                "no-cctest",
                "without-intl",
                "no-shared-roheap",
                "no-NODE-OPTIONS",
                "no-ssl"
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
            if self.settings.build_type == "Debug":
                args.append("--debug")

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
            rm(self, "*.TOC", "out/{}/lib".format(self.settings.build_type))

            if self.options.shared:
                if self.settings.os == "Macos":
                    self.copy(
                        "*.dylib",
                        src="out/{}".format(self.settings.build_type),
                        dst="lib",
                        keep_path=False,
                        symlinks=True,
                    )
                    self.run("ln -sf libnode*.dylib libnode.dylib", cwd=os.path.join(self.package_folder, "lib"))
                if self.settings.os == "Linux":
                    self.copy(
                        "libnode.so*",
                        src="out/{}/lib".format(self.settings.build_type),
                        dst="lib",
                        keep_path=False,
                        symlinks=True,
                    )
                    self.run("ln -sf libnode.so* libnode.so", cwd=os.path.join(self.package_folder, "lib"))

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["libnode", "v8_libplatform"]
        else:
            self.cpp_info.libs = ["node"]
