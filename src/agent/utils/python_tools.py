import importlib.util
import sys
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool
from langchain_experimental.tools import PythonREPLTool

python_repl = PythonREPLTool()


@tool
def execute_python(code: str) -> str:
    """Execute user-provided Python code string.
    
    Args:
        code: The Python code string to execute.
        
    Returns:
        Execution result or error message.
    """
    try:
        result = python_repl.run(code)
        return f"Execution successful:\n{result}"
    except Exception as e:
        return f"Execution error: {str(e)}"


SCRIPTS_DIR = Path(__file__).parent.parent.parent / "skills" / "python_execution" / "scripts"


def get_available_scripts() -> list[str]:
    """Get list of available predefined scripts."""
    if not SCRIPTS_DIR.exists():
        return []
    return [f.stem for f in SCRIPTS_DIR.glob("*.py") if f.name != "__init__.py"]


@tool
def run_script(
    script_name: str,
    args: Annotated[str, ""] = "",
) -> str:
    """Execute a predefined Python script from scripts directory.
    
    Args:
        script_name: Script filename without .py extension.
        args: Arguments to pass to the script (optional).
        
    Returns:
        Script execution result or error message.
    """
    available = get_available_scripts()
    
    if script_name not in available:
        return f"Script '{script_name}' not found. Available scripts: {', '.join(available) if available else 'none'}"
    
    script_path = SCRIPTS_DIR / f"{script_name}.py"
    
    try:
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[script_name] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, "main"):
                result = module.main(args) if args else module.main()
                return f"Script '{script_name}' executed successfully:\n{result}"
            else:
                return f"Script '{script_name}' has no main() function."
    except Exception as e:
        return f"Script execution error: {str(e)}"
