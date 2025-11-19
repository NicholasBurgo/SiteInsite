from fastapi import APIRouter, HTTPException
from backend.core.types import StartRunRequest, RunProgress
from backend.crawl.runner import RunManager
import os
import json
import shutil

router = APIRouter()
manager = RunManager()

@router.post("/start", response_model=dict)
async def start_run(req: StartRunRequest):
    run_id = await manager.start(req)
    return {"runId": run_id}

@router.get("/list")
async def list_runs():
    """List all available runs."""
    runs_dir = "runs"
    if not os.path.exists(runs_dir):
        return []
    
    runs = []
    try:
        for run_id in os.listdir(runs_dir):
            run_path = os.path.join(runs_dir, run_id)
            if os.path.isdir(run_path):
                meta_file = os.path.join(run_path, "meta.json")
                if os.path.exists(meta_file):
                    with open(meta_file, 'r') as f:
                        meta = json.load(f)
                    runs.append({
                        "runId": run_id,
                        "status": meta.get("status", "unknown"),
                        "started_at": meta.get("started_at", 0),
                        "completed_at": meta.get("completed_at"),
                        "url": meta.get("url")
                    })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing runs: {str(e)}")
    
    # Sort by started_at descending (newest first)
    runs.sort(key=lambda x: x["started_at"], reverse=True)
    return runs

@router.get("/{run_id}/progress", response_model=RunProgress)
async def run_progress(run_id: str):
    prog = await manager.progress(run_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Run not found")
    return prog

@router.post("/{run_id}/stop", response_model=dict)
async def stop_run(run_id: str):
    ok = await manager.stop(run_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"stopped": True}

@router.get("/{run_id}/meta")
async def get_run_meta(run_id: str):
    """Get run metadata."""
    meta_file = os.path.join("runs", run_id, "meta.json")
    if not os.path.exists(meta_file):
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        with open(meta_file, 'r') as f:
            meta = json.load(f)
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading meta file: {str(e)}")

@router.delete("/{run_id}/delete")
async def delete_run(run_id: str):
    """Delete a run and all its data."""
    run_dir = os.path.join("runs", run_id)
    if not os.path.exists(run_dir):
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        # Stop the run if it's still running
        await manager.stop(run_id)
        
        # Remove the entire run directory
        shutil.rmtree(run_dir)
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting run: {str(e)}")


@router.delete("/delete-all")
async def delete_all_runs():
    """Delete all runs and their data."""
    runs_dir = "runs"
    if not os.path.exists(runs_dir):
        return {"deleted": 0}

    deleted = 0
    errors = []

    for run_id in os.listdir(runs_dir):
        run_path = os.path.join(runs_dir, run_id)
        if not os.path.isdir(run_path):
            continue
        try:
            await manager.stop(run_id)
        except Exception as e:
            # Record stop errors but continue deletion attempt
            errors.append(f"{run_id}: stop failed ({e})")

        try:
            shutil.rmtree(run_path)
            deleted += 1
        except Exception as e:
            errors.append(f"{run_id}: delete failed ({e})")

    if errors:
        raise HTTPException(status_code=500, detail={"deleted": deleted, "errors": errors})

    return {"deleted": deleted}
