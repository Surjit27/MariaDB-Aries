from typing import List, Optional, Dict, Any, Tuple
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Try to use enhanced DB manager if available, else fallback
try:
    from db.enhanced_database_manager import EnhancedDatabaseManager as _DB
except Exception:
    from db.database_manager import DatabaseManager as _DB

try:
    from ai.gemini_integration import GeminiIntegration as _AI
except Exception:
    _AI = None  # AI optional


class TableColumn(BaseModel):
    name: str
    type: Optional[str] = None
    pk: Optional[bool] = None


class TableSchema(BaseModel):
    name: str
    columns: List[TableColumn]


class QueryRequest(BaseModel):
    database: Optional[str] = None
    sql: str


class QueryResult(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    duration_ms: Optional[int] = None
    affected: Optional[int] = None
    error: Optional[str] = None


class AiSessionMessage(BaseModel):
    role: str
    text: str


class AiRequest(BaseModel):
    mode: str
    selectedText: Optional[str] = None
    fullContext: Optional[str] = None
    sessionContext: Optional[List[AiSessionMessage]] = None
    database: Optional[str] = None


class AiResponse(BaseModel):
    text: str
    newSql: Optional[str] = None
    isComplete: Optional[bool] = True
    warnings: Optional[List[str]] = None


app = FastAPI(title="MariaDB-Aries API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dbm = _DB()
ai = _AI() if _AI else None


def _ensure_db(db: Optional[str]):
    if db:
        try:
            if getattr(dbm, "current_db", None) != db:
                if hasattr(dbm, "open_database"):
                    dbm.open_database(db)
                else:
                    # Some managers may set current_db directly
                    setattr(dbm, "current_db", db)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Unable to open database '{db}': {e}")


@app.get("/databases", response_model=List[str])
def list_databases():
    try:
        return dbm.get_databases()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/databases/{db}/tables", response_model=List[TableSchema])
def list_tables(db: str):
    _ensure_db(db)
    try:
        tables = dbm.get_tables()
        result: List[TableSchema] = []
        for t in tables:
            cols: List[TableColumn] = []
            try:
                if hasattr(dbm, "get_table_data"):
                    c, _ = dbm.get_table_data(t, limit=1)
                    cols = [TableColumn(name=name) for name in c]
            except Exception:
                pass
            result.append(TableSchema(name=t, columns=cols))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResult)
def execute_query(req: QueryRequest):
    _ensure_db(req.database)
    try:
        t0 = time.time()
        out = dbm.execute_query(req.sql)
        dt = int((time.time() - t0) * 1000)
        # Support either (columns, data, error) or (columns, data)
        columns: List[str]
        rows: List[Any]
        error: Optional[str] = None
        if isinstance(out, tuple) and len(out) == 3:
            columns, rows, error = out  # type: ignore
        elif isinstance(out, tuple) and len(out) == 2:
            columns, rows = out  # type: ignore
        else:
            columns, rows = ["Result"], [[str(out)]]  # fallback coercion
        # record log
        try:
            _LOGS.append({
                "ts": time.time(),
                "database": getattr(dbm, "current_db", None),
                "sql": req.sql,
                "duration_ms": dt,
                "error": error,
            })
        except Exception:
            pass
        return QueryResult(columns=columns, rows=rows, error=error, duration_ms=dt)
    except Exception as e:
        try:
            _LOGS.append({
                "ts": time.time(),
                "database": getattr(dbm, "current_db", None),
                "sql": req.sql,
                "duration_ms": 0,
                "error": str(e),
            })
        except Exception:
            pass
        return QueryResult(columns=["Error"], rows=[[str(e)]], error=str(e))


@app.post("/ai/generate", response_model=AiResponse)
def ai_generate(req: AiRequest):
    if not ai:
        raise HTTPException(status_code=503, detail="AI integration not available")
    _ensure_db(req.database)
    # Build minimal schema similarly to Tkinter flow
    schema = None
    try:
        if getattr(dbm, "current_db", None):
            tables = dbm.get_tables()
            table_schema: List[Dict[str, Any]] = []
            for t in tables:
                try:
                    cols, _ = dbm.get_table_data(t, limit=1)  # type: ignore
                    table_schema.append({
                        "table_name": t,
                        "columns": [{"name": c, "type": "TEXT"} for c in cols],
                    })
                except Exception:
                    table_schema.append({"table_name": t, "columns": []})
            schema = {"database_name": getattr(dbm, "current_db", None), "tables": table_schema, "relationships": []}
    except Exception:
        schema = None

    user_prompt = (req.selectedText or req.fullContext or "").strip()
    if not user_prompt:
        user_prompt = "Generate a relevant starter SQL query for this database."
    try:
        text = ai.generate_sql_query(user_prompt, schema)  # type: ignore
        text_str = str(text or "").replace("```sql", "").replace("```", "").strip()
        return AiResponse(text=text_str, newSql=text_str, isComplete=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


_LOGS: List[Dict[str, Any]] = []


@app.get("/logs")
def get_logs():
    return _LOGS[-200:]


