"""Choose a PyTorch device without requiring PyTorch for CPU utilities."""


def resolve_device(requested: str = "auto") -> str:
    if requested not in {"auto", "cpu", "cuda"}:
        raise ValueError("device must be auto, cpu or cuda")
    if requested == "cpu":
        return "cpu"
    try:
        import torch
    except ImportError:
        available = False
    else:
        available = torch.cuda.is_available()
    if requested == "cuda" and not available:
        raise RuntimeError("CUDA requested but unavailable; check PyTorch and GPU access")
    return "cuda" if available else "cpu"
