"""MessyDesk API for noteshrink (https://github.com/mzucker/noteshrink): cleans up scans of
notes by reducing them to a few colours, which removes paper texture, bleed-through and noise.

POST /process takes a `message` (task `clean`) and, in HTTP mode, the image as `content`; in disk
mode the image is read from message.file.path (see md_storage.py). /config, /help and /health come
from md_service.py.
"""
import json
import os
import uuid
from argparse import Namespace
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

import md_service
import md_storage
import noteshrink

app = FastAPI(title="MD-noteshrink", description="noteshrink for MessyDesk")

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# name: (default, low, high); percentages as in noteshrink's command line
NUMBER_PARAMS = {
    "num_colors": (8, 2, 64),
    "value_threshold": (25, 0, 100),
    "sat_threshold": (20, 0, 100),
    "sample_fraction": (5, 1, 100),
}
BOOL_PARAMS = {"white_bg": False, "saturate": True}


def options_from(params: dict) -> Namespace:
    """noteshrink's options from the task params (percentages become fractions)."""
    values = {}
    for name, (default, low, high) in NUMBER_PARAMS.items():
        raw = params.get(name, default)
        try:
            value = float(raw if raw not in (None, "") else default)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail=f"{name} must be a number")
        if not low <= value <= high:
            raise HTTPException(status_code=400, detail=f"{name} must be between {low} and {high}")
        values[name] = value
    flags = {}
    for name, default in BOOL_PARAMS.items():
        raw = params.get(name, default)
        flags[name] = raw if isinstance(raw, bool) else str(raw).strip().lower() in ("1", "true", "yes", "on")
    return Namespace(
        num_colors=int(values["num_colors"]),
        value_threshold=values["value_threshold"] / 100,
        sat_threshold=values["sat_threshold"] / 100,
        sample_fraction=values["sample_fraction"] / 100,
        white_bg=flags["white_bg"],
        saturate=flags["saturate"],
        quiet=True,
    )


def clean(image_path: str, output_path: str, options: Namespace) -> None:
    """One image through noteshrink: background colour, palette of the foreground, indexed PNG."""
    img, dpi = noteshrink.load(image_path)
    if img is None:
        raise HTTPException(status_code=400, detail="The input is not an image noteshrink can read")
    samples = noteshrink.sample_pixels(img, options)
    palette = noteshrink.get_palette(samples, options)
    labels = noteshrink.apply_palette(img, palette, options)
    noteshrink.save(output_path, labels, palette, dpi, options)


@app.get("/")
def root():
    return {"message": "noteshrink API for MessyDesk"}


@app.post("/process")
async def process(message: UploadFile = File(...), content: Optional[UploadFile] = File(None)):
    try:
        msg = json.loads((await message.read()).decode("utf-8"))
        if isinstance(msg, str):
            msg = json.loads(msg)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid message: {e}")
    task_id = (msg.get("task") or {}).get("id")
    if task_id != "clean":
        raise HTTPException(status_code=400, detail=f"Unsupported task: {task_id}")
    options = options_from((msg.get("task") or {}).get("params") or {})

    output_id = uuid.uuid4().hex
    output_path = os.path.join(OUTPUT_FOLDER, f"{output_id}.png")
    upload_path = None
    try:
        if content is not None:
            upload_path = os.path.join(UPLOAD_FOLDER, output_id + os.path.splitext(content.filename or "")[1])
            with open(upload_path, "wb") as f:
                f.write(await content.read())
            image_path = upload_path
        else:
            image_path = str(md_storage.message_input_path(msg))
        # numpy and k-means are CPU-bound - keep them off the event loop
        await run_in_threadpool(clean, image_path, output_path, options)
    except md_storage.StorageError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleaning failed: {e}")
    finally:
        if upload_path:
            try:
                os.remove(upload_path)
            except OSError:
                pass

    # <source label>.png, an image, as the elg adapter names a single HTTP output
    if content is None:
        entry = md_storage.stage_output(msg, output_path, f"{md_storage.source_label(msg)}.png", "image", "png")
        return md_storage.disk_response([entry])
    return {"response": {"type": "stored", "uri": f"/files/{output_id}.png"}}


@app.get("/files/{filename}")
def serve_file(filename: str, background_tasks: BackgroundTasks):
    output_dir = os.path.realpath(OUTPUT_FOLDER)
    file_path = os.path.realpath(os.path.join(output_dir, filename))
    # only files directly in OUTPUT_FOLDER; '../' paths could read any file
    if os.path.dirname(file_path) != output_dir or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    background_tasks.add_task(os.remove, file_path)
    return FileResponse(file_path, media_type="image/png")


# /config (service.json with the adapter of the storage mode), /help (help/index.md), /health
md_service.add_routes(app)


if __name__ == "__main__":
    import uvicorn

    print(f"storage mode: {md_storage.describe_mode()}")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "9023")))
