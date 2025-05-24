"""
Useful global methods
"""
def get_value_network(model_type):
        import importlib
        module_name = f"models.{model_type}.network"
        module = importlib.import_module(module_name)

        from pathlib import Path
        here = Path(__file__).resolve().parent
        latest_path = here / model_type / "latest.pth"
        return module, latest_path