"""Execute committed walkthroughs offline; Jupyter remains an optional dependency."""
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = (
    ROOT / "notebooks/01_data_and_eda.ipynb",
    ROOT / "notebooks/02_evaluation_walkthrough.ipynb",
)


@pytest.mark.offline
@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.stem)
def test_offline_notebook_executes(path, monkeypatch, tmp_path):
    nbclient = pytest.importorskip(
        "nbclient", reason="Optional notebook runner missing; run make notebooks or uv run --with jupyter --with nbclient pytest tests/test_notebooks.py"
    )
    nbformat = pytest.importorskip("nbformat", reason="Optional notebook format package missing; run make notebooks")
    pytest.importorskip("ipykernel", reason="Optional Python notebook kernel missing; run make notebooks")
    from jupyter_client import KernelManager

    # The child kernel uses this test's environment, including uv's optional packages.
    manager = KernelManager(kernel_name="python3")
    manager.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    for name in tuple(os.environ):
        if name.endswith(("_API_KEY", "_API_TOKEN")) or name in {"OPENAI_BASE_URL", "LABOURLENS_API_KEY"}:
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("MPLBACKEND", "Agg")
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    notebook = nbformat.read(path, as_version=4)
    client = nbclient.NotebookClient(
        notebook,
        km=manager,
        timeout=180,
        allow_errors=False,
        resources={"metadata": {"path": str(ROOT)}},
    )
    try:
        client.execute()
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
        if client.kc is not None:
            client.kc.stop_channels()
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code" and cell.source.strip()]
    assert code_cells, "A walkthrough must contain executable analysis"
    assert all(cell.execution_count is not None for cell in code_cells)
    assert not any(output.output_type == "error" for cell in code_cells for output in cell.outputs)
