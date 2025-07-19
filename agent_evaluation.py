from lmnr import evaluate, Laminar, Instruments
from automation_agent import run_bunnings_navigator
import os
from dotenv import load_dotenv

load_dotenv()

Laminar.initialize(
    project_api_key=os.getenv("LMNR_PROJECT_API_KEY"),
    base_url="http://localhost",
    http_port=8000,
    grpc_port=8001,
    disable_batch=True,
    disabled_instruments={Instruments.BROWSER_USE}
)

def success_evaluator(output: str, target: str) -> int:
    """1.0 if the output matches the target, else 0.0."""
    return 1 if target in output else 0

# def duration_evaluator(trace):
#     """Total runtime in seconds."""
#     return (trace.end_time - trace.start_time).total_seconds()

# def recovery_evaluator(trace):
#     """Error recovery efficiency: 1/(error_count+1)."""
#     errors = sum(1 for e in trace.events if e.level == "ERROR")
#     return 1.0 / (errors + 1)

async def main_executor(data):
    return await run_bunnings_navigator(**data)

evaluate(
    data=[
        {
            "data": {
                "product_name": "chair",
                "provider": "openai",
                "street_address": "123 Fake St",
                "unit": None,
                "suburb_address": "Sydney",
                "state": "NSW",
                "postcode": "2000",
            },
            "target": "SUCCESS"
        },
    ],
    executor=main_executor,
    evaluators={
        "success_rate": success_evaluator,
        # "duration_seconds": duration_evaluator,
        # "recovery_efficiency": recovery_evaluator,
    },
    project_api_key=os.getenv("LMNR_PROJECT_API_KEY"),
)
