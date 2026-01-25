# Generates STL files from SolidWorks part files by varying dimensions specified in a dictionary.
# Requires to be run from the directory containing the SolidWorks part file and a PowerShell script `export_solidworks_to_stl.ps1` for exporting to STL.
# Solidworks part must have global dimensions linked to a text file named `dimensions.txt.
# Requires SolidWorks present on the system

# Povilas Sauciuvienas 2025-01-25

import subprocess
from itertools import product


def name_from_parms(params) -> str:
    return f"c{params['channel_width']}w{params['channel_wall_width']}"


def update_dims_txt(params) -> None:
    with open("dimensions.txt", "w") as f:
        for key, value in params.items():
            f.write(f"{key}={value}\n")


def generate_stl(
    params,
    solidworks_part_path: str,
    out_folder="generated_STLs",
    pws_script_path="export_solidworks_to_stl.ps1",
):
    """Generates an STL file from a SolidWorks part file with specified parameters."""

    params = {k: str(v).lstrip("0") for k, v in params.items()}
    filename = name_from_parms(params)
    update_dims_txt(params)

    output_path = f"{out_folder}/{filename}.stl"

    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            pws_script_path,
            solidworks_part_path,
            output_path,
        ],
        check=True,
    )


def generate_param_grid(d: dict[str, list[float]]) -> dict[str, float]:
    """Generates all combinations of parameters from the given dictionary."""
    keys = d.keys()
    for combo in product(*d.values()):
        yield dict(list(zip(keys, combo)))


if __name__ == "__main__":
    dimensions = {
        "channel_width": [0.2, 0.4, 0.6],
        "channel_wall_width": [0.2, 0.4, 0.6],
    }

    for params in generate_param_grid(dimensions):
        generate_stl(
            params, out_folder="generated_STLs", solidworks_part_path="wall_test.SLDPRT"
        )
