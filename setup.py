import os
import platform
import stat

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

PACKAGE_NAME = "agentsociety"
SIM_VERSION = "v1.4.3"
BIN_SOURCES = {
    "agentsociety-sim": {
        "linux_x86_64": f"https://agentsociety.obs.cn-north-4.myhuaweicloud.com/agentsociety-sim/{SIM_VERSION}/agentsociety-sim-noproj-linux-amd64",
        "darwin_arm64": f"https://agentsociety.obs.cn-north-4.myhuaweicloud.com/agentsociety-sim/{SIM_VERSION}/agentsociety-sim-noproj-darwin-arm64",
    },
}


class BinExtension(Extension):
    def __init__(self, name: str, type: str):
        # if type == "download" -> download the binary from url
        super().__init__(name, sources=[])
        self.name = name
        self.type = type


class BuildExtension(build_ext):
    def run(self):
        system = platform.system()
        machine = platform.machine()
        if system == "Linux":
            plat_dir = "linux"
            if machine == "x86_64":
                arch = "x86_64"
            else:
                print("Unsupported architecture on Linux")
                raise Exception("Unsupported architecture on Linux")
        elif system == "Darwin" and machine.startswith("arm"):
            plat_dir = "darwin"
            arch = "arm64"
        else:
            print("Unsupported platform")
            raise Exception("Unsupported platform")
        # build the extension
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(PACKAGE_NAME)))
        for ext in self.extensions:
            if ext.type == "download":
                self._download_bin(
                    ext.name, plat_dir, arch, os.path.join(extdir, PACKAGE_NAME)
                )

    def _download_bin(self, binary_name, plat_dir, arch, bin_dir):
        import os

        import requests

        url = BIN_SOURCES[binary_name].get(f"{plat_dir}_{arch}")
        if url:
            response = requests.get(url)
            if response.status_code == 200:
                binary_path = os.path.join(bin_dir, binary_name)
                binary_path = os.path.abspath(binary_path)
                # print("try to download binary to", binary_path, flush=True)
                with open(binary_path, "wb") as f:
                    f.write(response.content)
                os.chmod(binary_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                print(f"Downloaded {binary_name} to {binary_path}")
            else:
                print(f"Download failed for {binary_name}")
                raise Exception(f"Download failed for {binary_name}")
        else:
            print(f"No binary found for {binary_name}")
            raise Exception(f"No binary found for {binary_name}")


setup(
    ext_modules=[
        BinExtension("agentsociety-sim", "download"),
    ],
    cmdclass=dict(build_ext=BuildExtension),
)

# # How to run it to build the distribution package
# pip install build
# python -m build
#
# use cibuildwheel to build wheels for multiple platforms
# pip install cibuildwheel
# cibuildwheel
