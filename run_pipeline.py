import json

from salesflow.pipeline import run_pipeline


if __name__ == "__main__":
    result = run_pipeline()
    print("\nETL PIPELINE COMPLETED")
    print(json.dumps(result, indent=2))