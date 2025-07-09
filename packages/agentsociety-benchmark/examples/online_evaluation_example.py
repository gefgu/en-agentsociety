"""
Online Evaluation System Integration Example

This example demonstrates how to integrate agentsociety-benchmark tool
into an online evaluation system that receives uploaded results.pkl files.

- **Description**:
    - Shows how to use the new evaluate_from_file_object method
    - Demonstrates handling file objects from web uploads
    - Provides error handling and result processing
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import json

from agentsociety_benchmark.runner import BenchmarkRunner
from agentsociety_benchmark.cli.config import BenchmarkConfig


class OnlineEvaluationService:
    """
    Online evaluation service for processing uploaded results.pkl files.
    
    - **Description**:
        - Handles file uploads from web interface
        - Processes results.pkl files using agentsociety-benchmark
        - Returns evaluation results in a standardized format
    """
    
    def __init__(self, config_path: str, datasets_path: Optional[str] = None):
        """
        Initialize the online evaluation service.
        
        - **Args**:
            - `config_path` (str): Path to benchmark configuration file
            - `datasets_path` (Optional[str]): Path to datasets directory
        """
        self.config_path = Path(config_path)
        self.datasets_path = Path(datasets_path) if datasets_path else None
        
        # Initialize benchmark runner
        self.runner = BenchmarkRunner(config=BenchmarkConfig.model_validate_json(self.config_path.read_text()))
    
    async def evaluate_uploaded_file(self, 
                                   file_object: bytes, 
                                   task_name: str,
                                   output_file: Optional[str] = None,
                                   save_to_database: bool = False) -> Dict[str, Any]:
        """
        Evaluate an uploaded results.pkl file.
        
        - **Description**:
            - Processes uploaded file object containing benchmark results
            - Runs evaluation using the specified task
            - Returns evaluation results and metadata
            
        - **Args**:
            - `file_object` (bytes): Uploaded file content as bytes
            - `task_name` (str): Name of the benchmark task to evaluate
            - `output_file` (Optional[str]): Path to save evaluation results
            - `save_to_database` (bool): Whether to save results to database
            
        - **Returns**:
            - `Dict[str, Any]`: Evaluation results and status information
        """
        try:
            # Validate task name
            available_tasks = self.runner.list_available_tasks()
            if task_name not in available_tasks:
                return {
                    "success": False,
                    "error": f"Task '{task_name}' not found. Available tasks: {available_tasks}",
                    "available_tasks": available_tasks
                }
            
            # Set output file path if specified
            output_path = None
            if output_file:
                output_path = Path(output_file)
            
            # Run evaluation using the new file object method
            result = await self.runner.evaluate_from_file_object(
                tenant_id="evaluation_tenant",
                task_name=task_name,
                file_object=file_object,
                datasets_path=self.datasets_path,
                output_file=output_path,
                save_results=save_to_database
            )
            
            return {
                "success": True,
                "task_name": task_name,
                "evaluation_result": result["evaluation_result"],
                "output_file": result.get("output_file"),
                "message": f"Evaluation completed successfully for task: {task_name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task_name": task_name,
                "message": f"Evaluation failed for task: {task_name}"
            }
    
    def get_available_tasks(self) -> Dict[str, Any]:
        """
        Get list of available benchmark tasks.
        
        - **Description**:
            - Returns all available benchmark tasks with their information
            - Useful for web interface to show available options
            
        - **Returns**:
            - `Dict[str, Any]`: Available tasks and their information
        """
        try:
            available_tasks = self.runner.list_available_tasks()
            task_info = {}
            
            for task_name in available_tasks:
                info = self.runner.get_task_info(task_name)
                task_info[task_name] = info
            
            return {
                "success": True,
                "available_tasks": available_tasks,
                "task_info": task_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "available_tasks": [],
                "task_info": {}
            }
    
    def validate_file_format(self, file_object: bytes) -> Dict[str, Any]:
        """
        Validate uploaded file format.
        
        - **Description**:
            - Validates that the uploaded file is a valid results.pkl file
            - Checks file structure and metadata without running evaluation
            
        - **Args**:
            - `file_object` (bytes): Uploaded file content as bytes
            
        - **Returns**:
            - `Dict[str, Any]`: Validation result and file information
        """
        try:
            from agentsociety_benchmark.cli.commands.evaluate import load_results_from_file_object
            
            # Try to load the file
            results, metadata = load_results_from_file_object(file_object)
            
            # Extract basic information
            task_name = metadata.get("task_name", "Unknown")
            tenant_id = metadata.get("tenant_id", "Unknown")
            exp_id = metadata.get("exp_id", "Unknown")
            llm = metadata.get("llm", "Unknown")
            agent = metadata.get("agent", "Unknown")
            mode = metadata.get("mode", "Unknown")
            
            return {
                "success": True,
                "file_valid": True,
                "task_name": task_name,
                "tenant_id": tenant_id,
                "exp_id": exp_id,
                "llm": llm,
                "agent": agent,
                "mode": mode,
                "results_count": len(results) if isinstance(results, list) else "N/A",
                "message": "File format is valid"
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_valid": False,
                "error": str(e),
                "message": "Invalid file format"
            }


# Example usage in a web application
async def example_web_integration():
    """
    Example of how to integrate with a web application.
    
    - **Description**:
        - Shows how to use the OnlineEvaluationService in a web context
        - Demonstrates file upload handling and result processing
    """
    
    # Initialize the evaluation service
    evaluation_service = OnlineEvaluationService(
        config_path="path/to/benchmark_config.yml",
        datasets_path="path/to/datasets"
    )
    
    # Example: Get available tasks (for web interface dropdown)
    tasks_info = evaluation_service.get_available_tasks()
    print("Available tasks:", tasks_info)
    
    # Example: Validate uploaded file
    # In a real web app, this would be the uploaded file content
    with open("example_results.pkl", "rb") as f:
        uploaded_file_content = f.read()
    
    validation_result = evaluation_service.validate_file_format(uploaded_file_content)
    print("File validation:", validation_result)
    
    if validation_result["file_valid"]:
        # Example: Run evaluation
        task_name = validation_result["task_name"]
        evaluation_result = await evaluation_service.evaluate_uploaded_file(
            file_object=uploaded_file_content,
            task_name=task_name,
            output_file="evaluation_output.json",
            save_to_database=False
        )
        
        print("Evaluation result:", evaluation_result)
        
        if evaluation_result["success"]:
            final_score = evaluation_result["evaluation_result"].get("final_score", "N/A")
            print(f"Final score: {final_score}")


# Example: Simple web API endpoint (pseudo-code)
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI()
evaluation_service = OnlineEvaluationService(
    config_path="config.yml",
    datasets_path="datasets"
)

@app.post("/api/evaluate")
async def evaluate_results(
    file: UploadFile = File(...),
    task_name: str = None,
    save_to_db: bool = False
):
    # Read uploaded file
    file_content = await file.read()
    
    # Validate file format
    validation = evaluation_service.validate_file_format(file_content)
    if not validation["file_valid"]:
        return JSONResponse(
            status_code=400,
            content={"error": validation["error"]}
        )
    
    # Use task name from file if not provided
    if not task_name:
        task_name = validation["task_name"]
    
    # Run evaluation
    result = await evaluation_service.evaluate_uploaded_file(
        file_object=file_content,
        task_name=task_name,
        save_to_database=save_to_db
    )
    
    return JSONResponse(content=result)

@app.get("/api/tasks")
async def get_available_tasks():
    return JSONResponse(content=evaluation_service.get_available_tasks())
"""


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_web_integration()) 