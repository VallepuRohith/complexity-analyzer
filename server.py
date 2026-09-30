import os
import textwrap
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

from complexity_analyzer.analyzer import analyze_code

app = FastAPI(title="Complexity Analyzer API", version="1.0.0")

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    code: str


def analyze_source_code(source: str) -> Dict[str, Any]:
    cleaned_source = textwrap.dedent(source).strip()
    if not cleaned_source:
        return {
            "success": False,
            "error": "Code snippet cannot be empty.",
        }

    try:
        result = analyze_code(cleaned_source)
        res_dict = result.to_dict()
        details = res_dict.get("details", {})
        
        return {
            "success": True,
            "time_complexity": res_dict.get("time", "O(1)"),
            "space_complexity": res_dict.get("space", "O(1)"),
            "explanation": res_dict.get("explanation", "Analysis completed."),
            "metrics": {
                "max_loop_depth": details.get("max_loop_depth", 0),
                "max_input_loop_depth": details.get("max_input_loop_depth", 0),
                "for_loops": details.get("for_loops", 0),
                "while_loops": details.get("while_loops", 0),
                "constant_loops": details.get("constant_loops", 0),
                "logarithmic_loops": details.get("logarithmic_loops", 0),
                "input_variables": sorted(list(details.get("input_variables", []))),
                "allocations": details.get("allocations", []),
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error analyzing code: {str(e)}",
        }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "complexity-analyzer-backend"}


@app.post("/api/analyze")
def analyze_endpoint(request: AnalyzeRequest):
    return analyze_source_code(request.code)


@app.get("/api/examples")
def get_examples():
    return [
        {
            "id": "sample_test",
            "name": "Sample (O(n) Time, O(n²) Space)",
            "description": "Allocation inside loop scaling with input size",
            "code": textwrap.dedent("""\
                def test(arr):
                    for x in arr:
                        temp = [0] * len(arr)

                    return 0
            """)
        },
        {
            "id": "constant_time",
            "name": "O(1) Constant Time",
            "description": "Direct index lookup or arithmetic calculation without loops",
            "code": textwrap.dedent("""\
                def get_first_element(arr):
                    if len(arr) == 0:
                        return None
                    first = arr[0]
                    return first * 2
            """)
        },
        {
            "id": "constant_loops",
            "name": "O(1) Fixed Loop Bounds",
            "description": "Nested loops iterating over constant ranges independent of input size",
            "code": textwrap.dedent("""\
                def fixed_iterations():
                    total = 0
                    for i in range(10):
                        for j in range(5):
                            total += i * j
                    return total
            """)
        },
        {
            "id": "linear_search",
            "name": "O(n) Linear Search",
            "description": "Single loop traversing elements once with O(1) auxiliary space",
            "code": textwrap.dedent("""\
                def linear_search(arr, target):
                    for item in arr:
                        if item == target:
                            return True
                    return False
            """)
        },
        {
            "id": "binary_search",
            "name": "O(log n) Binary Search",
            "description": "While loop halving search space on each iteration",
            "code": textwrap.dedent("""\
                def binary_search(arr, target):
                    low = 0
                    high = len(arr) - 1
                    while low <= high:
                        mid = (low + high) // 2
                        if arr[mid] == target:
                            return mid
                        elif arr[mid] < target:
                            low = mid + 1
                        else:
                            high = mid - 1
                    return -1
            """)
        },
        {
            "id": "quadratic_bubble_sort",
            "name": "O(n²) Nested Loops",
            "description": "Two nested loops comparing adjacent elements",
            "code": textwrap.dedent("""\
                def bubble_sort(arr):
                    n = len(arr)
                    for i in range(n):
                        for j in range(0, n - i - 1):
                            if arr[j] > arr[j + 1]:
                                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    return arr
            """)
        },
        {
            "id": "cubic_matrix",
            "name": "O(n³) 3D Loop Matrix",
            "description": "Triply nested loops multiplying two square matrices",
            "code": textwrap.dedent("""\
                def matrix_multiply(A, B):
                    n = len(A)
                    for i in range(n):
                        for j in range(n):
                            for k in range(n):
                                pass
                    return 0
            """)
        },
        {
            "id": "linear_space",
            "name": "O(n) Space - Dynamic List",
            "description": "Allocates a new collection scaling with input array size",
            "code": textwrap.dedent("""\
                def duplicate_array(arr):
                    clone = [0] * len(arr)
                    for i in range(len(arr)):
                        clone[i] = arr[i]
                    return clone
            """)
        },
        {
            "id": "quadratic_space_retention",
            "name": "O(n²) Space - Matrix Allocation in Loop",
            "description": "Allocating vectors inside a loop and appending to a matrix",
            "code": textwrap.dedent("""\
                def generate_matrix(arr):
                    matrix = []
                    for x in arr:
                        row = [0] * len(arr)
                        matrix.append(row)
                    return matrix
            """)
        }
    ]



# Serve frontend static assets if built (for all-in-one web deployment)
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from fastapi import HTTPException

    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import os
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("ENV", "development").lower() != "production"
    uvicorn.run("server:app", host=host, port=port, reload=reload)

