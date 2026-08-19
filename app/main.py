from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import PriorityRequest, ReportRequest, RoleFamily, SprintRequest
from app.services.jd_parser import build_matrix, dataset_summary, load_jds
from app.services.scoring import rank_priorities
from app.services.sprint import build_report, generate_sprint


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw_jds"
STATIC_DIR = ROOT / "static"

app = FastAPI(title="Growth Mini", version="0.1.0")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/dataset")
def dataset(role_family: RoleFamily = Query(default="all")) -> dict:
    return dataset_summary(load_jds(DATA_DIR, role_family))


@app.get("/api/matrix")
def matrix(role_family: RoleFamily = Query(default="all")) -> dict:
    records = load_jds(DATA_DIR, role_family)
    return {"summary": dataset_summary(records), "matrix": build_matrix(records)}


@app.post("/api/priorities")
def priorities(request: PriorityRequest) -> dict:
    records = load_jds(DATA_DIR, request.role_family)
    matrix_rows = build_matrix(records)
    evidence = [item.model_dump() for item in request.evidence]
    return {"priorities": rank_priorities(matrix_rows, evidence)}


@app.post("/api/sprint")
def sprint(request: SprintRequest) -> dict:
    return generate_sprint(request.skill, request.daily_minutes)


@app.post("/api/report")
def report(request: ReportRequest) -> dict:
    return build_report(request.estimated_minutes, [item.model_dump() for item in request.checkins])


@app.get("/")
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
