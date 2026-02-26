# Generates STL files from SolidWorks part/assembly files by varying dimensions specified in a dictionary.
# Requires running from a repo where SolidWorks model exists.
# SolidWorks model must have global dimensions linked to a text file named `dimensions.txt`.
# Requires a PowerShell script `export_solidworks_to_stl.ps1` for exporting to STL.
# Requires SolidWorks present on the system

import os
import subprocess
from itertools import product
from typing import Dict, Iterable, List, Optional


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def update_dims_txt(params: Dict[str, float], model_path: str) -> str:
    """
    Writes dimensions.txt next to the SolidWorks model file (recommended),
    because many SW setups reference a file relative to the model directory.
    """
    model_dir = os.path.dirname(os.path.abspath(model_path))
    txt_path = os.path.join(model_dir, "dimensions.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for key, value in params.items():
            f.write(f"{key}={value}\n")
    return txt_path


def generate_param_grid(d: Dict[str, List[float]]) -> Iterable[Dict[str, float]]:
    """Generates all combinations of parameters from the given dictionary."""
    keys = list(d.keys())
    for combo in product(*d.values()):
        yield dict(zip(keys, combo))


def name_from_params(params: Dict[str, float]) -> str:
    """
    Stable, filesystem-safe name. Converts 4.15 -> 4p15.
    """
    def fmt(x: float) -> str:
        s = str(x)
        if s.startswith("0."):
            s = s[1:]
     
        return s

    ir = fmt(params["inner_radius"])
    oscr = fmt(params["outer_screw"])
    iscr = fmt(params["inner_screw"])
    return f"d{ir}o{oscr}i{iscr}"


def generate_stl(
    params: Dict[str, float],
    solidworks_model_path: str,
    out_folder: str = "generated_STLs",
    pws_script_path: str = r"src\export_solidworks_to_stl.ps1",
    filename: Optional[str] = None,
) -> str:
    """
    Generates an STL file from a SolidWorks part/assembly file with specified parameters.
    Returns the output STL path.
    """
    model_path = os.path.abspath(solidworks_model_path)
    script_path = os.path.abspath(pws_script_path)
    out_dir = ensure_dir(os.path.abspath(out_folder))

    if filename is None:
        base = os.path.splitext(os.path.basename(model_path))[0]
        filename = base

    # Write dimensions next to the model file
    update_dims_txt(params, model_path)

    output_path = os.path.join(out_dir, f"{filename}.stl")

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        script_path,
        model_path,
        output_path,
    ]

    p = subprocess.run(cmd, text=True, capture_output=True)
    print("returncode:", p.returncode)
    if p.stdout.strip():
        print("stdout:\n", p.stdout)
    if p.stderr.strip():
        print("stderr:\n", p.stderr)

    p.check_returncode()

    if not os.path.exists(output_path):
        raise RuntimeError(f"Export reported success but STL not found: {output_path}")

    return output_path


if __name__ == "__main__":
    dimensions: Dict[str, List[float]] = {
        "inner_radius": [4.15, 4],
        "outer_screw":  [7.8, 7.0, 6.0],
        "inner_screw":  [6.6, 6.0, 5.0],
    }

    # Point these at the actual SolidWorks file and desired output directory
    solidworks_model_path = r"slug_electroporator\2026_02_12\lock_test.SLDASM"  # or .SLDPRT
    out_folder = r"slug_electroporator\2026_02_12\stls"

    for params in generate_param_grid(dimensions):
        stl_path = generate_stl(
            params=params,
            solidworks_model_path=solidworks_model_path,
            out_folder=out_folder,
            filename=name_from_params(params),
        )
        print("Saved:", stl_path)
