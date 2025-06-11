import os
import platform
import stat
from pathlib import Path

import requests
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

PACKAGE_NAME = "agentsociety"
SIM_VERSION = "v1.4.3"
BIN_SOURCES = {
    "agentsociety-sim": {
        "linux_x86_64": f"https://agentsociety.obs.cn-north-4.myhuaweicloud.com/agentsociety-sim/{SIM_VERSION}/agentsociety-sim-noproj-linux-amd64",
        "darwin_arm64": f"https://agentsociety.obs.cn-north-4.myhuaweicloud.com/agentsociety-sim/{SIM_VERSION}/agentsociety-sim-noproj-darwin-arm64",
    },
}

def download_binary(binary_name: str, plat_dir: str, arch: str, bin_dir: str) -> None:
    url = BIN_SOURCES[binary_name].get(f"{plat_dir}_{arch}")
    if not url:
        raise Exception(f"No binary found for {binary_name}")
    
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Download failed for {binary_name}")
    
    binary_path = os.path.join(bin_dir, binary_name)
    binary_path = os.path.abspath(binary_path)
    
    with open(binary_path, "wb") as f:
        f.write(response.content)
    os.chmod(binary_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    print(f"Downloaded {binary_name} to {binary_path}")

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        system = platform.system()
        machine = platform.machine()
        
        if system == "Linux":
            plat_dir = "linux"
            if machine == "x86_64":
                arch = "x86_64"
            else:
                raise Exception("Unsupported architecture on Linux")
        elif system == "Darwin" and machine.startswith("arm"):
            plat_dir = "darwin"
            arch = "arm64"
        else:
            raise Exception("Unsupported platform")
        
        # 设置为平台特定的wheel
        build_data['infer_tag'] = True
        build_data['pure_python'] = False
        
        bin_dir = os.path.join(self.root, PACKAGE_NAME)
        os.makedirs(bin_dir, exist_ok=True)
        
        download_binary("agentsociety-sim", plat_dir, arch, bin_dir) 