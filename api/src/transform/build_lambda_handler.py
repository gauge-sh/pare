from __future__ import annotations

from pathlib import Path
from string import Template

template_path = Path(__file__).parent / "template.py"

try:
    template_content = template_path.read_text()
except Exception as e:
    raise FileNotFoundError(
        "Could not find required 'template.py' to build lambda handlers."
    ) from e

template = Template(template_content)


def build_lambda_handler(symbol_path: str, output_path: Path):
    try:
        mod_path, target_symbol = symbol_path.split(":")
    except ValueError:  # not enough values to unpack/too many values to unpack
        raise ValueError(
            f"Could not resolve module path and target symbol from: '{symbol_path}'"
        )
    filled_content = template.substitute(mod_path=mod_path, target_symbol=target_symbol)
    output_path.write_text(filled_content)
