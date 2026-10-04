"""Small smoke check to run after opening a development container."""

import argparse
import os
import platform
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is unavailable")
    args = parser.parse_args()
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print(f"Working directory: {os.getcwd()}")
    try:
        import torch
    except ImportError:
        print("PyTorch: not installed (expected in the CPU container)")
        if args.require_cuda:
            parser.exit(1, "CUDA check failed: PyTorch is not installed\n")
    else:
        print(f"PyTorch: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            value = (torch.ones(1, device="cuda") + 1).item()
            print(f"CUDA tensor smoke check: {value == 2}")
        elif args.require_cuda:
            parser.exit(1, "CUDA check failed: CUDA is unavailable\n")


if __name__ == "__main__":
    main()
