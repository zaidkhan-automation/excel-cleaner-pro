# main.py
# FastAPI backend with /clean endpoint that uses the processors above.
# Run: uvicorn main:app --host 0.0.0.0 --port 8001

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
import io
import json

from backend.utils import read_upload_to_df, df_to_bytes, build_summary
from backend.processors.type_normalizer import normalize_types
from backend.processors.dedupe_engine import dedupe_dataframe
from backend.processors.ai_cleaner import apply_business_rules

app = FastAPI(title="Excel Cleaner - Diamond Engine")


@app.post("/clean")
async def clean_file(file: UploadFile = File(...), out_format: str = "xlsx"):
    try:
        df_before = read_upload_to_df(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 1: type normalization
    df_types_normalized, type_issues = normalize_types(df_before)

    # Step 2: apply business rules
    df_business, business_issues = apply_business_rules(df_types_normalized)

    # Step 3: dedupe
    df_deduped, dedupe_issues = dedupe_dataframe(df_business, threshold=0.88)

    # Build combined issues
    issues = {"type_issues": type_issues, "business_issues": business_issues, "dedupe_issues": dedupe_issues}

    # Convert to requested format
    try:
        content_bytes, ext = df_to_bytes(df_deduped, to_format=out_format)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to convert output: {e}")

    # Prepare summary JSON for inline use
    summary = build_summary(df_before, df_deduped, issues)

    # Return a streaming response with attachments: file + summary header
    filename = f"cleaned_{file.filename.rsplit('.',1)[0]}.{ext}"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "X-Cleaner-Summary": json.dumps(summary)
    }
    return StreamingResponse(io.BytesIO(content_bytes), media_type="application/octet-stream", headers=headers)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "backend_port": 8001})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
