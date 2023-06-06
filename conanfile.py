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
                "--without-node-snapshot"
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

            autotools.configure(args=args, vars=build_vars, use_default_install_dirs=False)
            autotools.make(vars=build_vars)

    def package(self):
        self.run(
            "python3 tools/install.py install {0} /. {1}".format(self.package_folder, self.settings.build_type))
        if self.settings.os == "Windows":
            rm(self, "node.exe", os.path.join(self.package_folder, "bin"))
        else:
            rm(self, "node", os.path.join(self.package_folder, "bin"))
            if self.options.shared:
                if self.settings.os == "Macos":
                    self.run("ln -sf libnode*.dylib libnode.dylib", cwd=os.path.join(self.package_folder, "lib"))
                elif self.settings.os == "Linux":
                    self.run("ln -sf libnode.so* libnode.so", cwd=os.path.join(self.package_folder, "lib"))

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["libnode", "v8_libplatform"]
        else:
            self.cpp_info.libs = ["node"]
