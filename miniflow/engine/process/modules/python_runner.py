import importlib.util
import json
from queue import Queue


def python_runner(item: json, output_queue: Queue):
    execution_id = item.get("execution_id", "UNKNOWN")
    node_id = item.get("node_id", "UNKNOWN")
    
    print(f"[PYTHON_RUNNER] Starting task: execution_id={execution_id}, node_id={node_id}")
    print(f"[PYTHON_RUNNER] Task context: {item.get('context', {})}")
    
    try:
        script_path = item.get("script_path")
        if not script_path:
            raise ValueError("script_path is missing")

        print(f"[PYTHON_RUNNER] Loading script: {script_path}")
        module_name = script_path.split("/")[-1].replace(".py", "")

        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for module at {script_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "module"):
            raise AttributeError("The module must contain a 'module()' function")

        run_module = module.module()

        if not hasattr(run_module, "run"):
            raise AttributeError("The object returned by 'module()' must have a 'run()' method")

        context = item.get("context")

        if isinstance(context, str):
            context = json.loads(context)

        print(f"[PYTHON_RUNNER] Executing script with context: {context}")
        result = run_module.run(context)
        print(f"[PYTHON_RUNNER] Script result: {result}")
        
        item["result_data"] = result
        item["status"] = "SUCCESS"

    except FileNotFoundError:
        print(f"[PYTHON_RUNNER] Script file not found: {script_path}")
        item["error_message"] = "Script file not found"
        item["status"] = "FAILED"
    except ImportError as e:
        print(f"[PYTHON_RUNNER] Import error: {str(e)}")
        item["error_message"] = f"Import error: {str(e)}"
        item["status"] = "FAILED"
    except AttributeError as e:
        print(f"[PYTHON_RUNNER] Attribute error: {str(e)}")
        item["error_message"] = f"Attribute error: {str(e)}"
        item["status"] = "FAILED"
    except ValueError as e:
        print(f"[PYTHON_RUNNER] Value error: {str(e)}")
        item["error_message"] = f"Value error: {str(e)}"
        item["status"] = "FAILED"
    except (json.JSONDecodeError, TypeError) as e:
        print(f"[PYTHON_RUNNER] JSON error: {str(e)}")
        item["error_message"] = f"JSON error: {str(e)}"
        item["status"] = "FAILED"
    except Exception as e:
        print(f"[PYTHON_RUNNER] Unexpected error: {str(e)}")
        item["error_message"] = f"Unexpected error: {str(e)}"
        item["status"] = "FAILED"

    print(f"[PYTHON_RUNNER] Task completed: execution_id={execution_id}, node_id={node_id}, status={item.get('status')}")
    output_queue.put(item)
