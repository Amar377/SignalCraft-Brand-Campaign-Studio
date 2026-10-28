
"""SignalCraft: multi-provider AI Brand & Campaign Studio API."""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("signalcraft")

DB_PATH = Path(
    os.getenv("SIGNALCRAFT_DB_PATH", str(BASE_DIR / "signalcraft.db"))
)
if not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH

AI_PROVIDER_ORDER = [
    item.strip().lower()
    for item in os.getenv("AI_PROVIDER_ORDER", "groq").split(",")
    if item.strip()
]


class CampaignPlan(BaseModel):
    campaign_name: str
    campaign_objective: str
    target_audience: Optional[str] = None
    key_message: Optional[str] = None
    channels: list[str] = Field(default_factory=list)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None
    call_to_action: Optional[str] = None
    missing_information: list[str] = Field(default_factory=list)
    campaign_summary: str

    @model_validator(mode="after")
    def check_dates(self):
        if (
            self.start_date
            and self.end_date
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class CalendarEntry(BaseModel):
    title: str
    publish_date: Optional[date] = None
    platform: str
    content_type: str
    objective: str
    draft_caption: str
    call_to_action: Optional[str] = None
    hashtags: list[str] = Field(default_factory=list)
    status: Literal["planned", "draft", "approved", "published"] = "planned"


class ContentCalendar(BaseModel):
    campaign_name: str
    rationale: str
    entries: list[CalendarEntry] = Field(min_length=1)


class BrandProfile(BaseModel):
    brand_name: str
    industry: Optional[str] = None
    products_services: list[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    brand_voice: list[str] = Field(default_factory=list)
    preferred_phrases: list[str] = Field(default_factory=list)
    phrases_to_avoid: list[str] = Field(default_factory=list)
    differentiators: list[str] = Field(default_factory=list)
    visual_guidance: Optional[str] = None
    missing_information: list[str] = Field(default_factory=list)
    profile_summary: str


class PerformanceInsight(BaseModel):
    campaign_name: Optional[str] = None
    reporting_period: Optional[str] = None
    key_metrics: list[dict] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence_notes: list[str] = Field(default_factory=list)
    summary: str


class PlatformDraft(BaseModel):
    platform: str
    format: str
    headline: Optional[str] = None
    body: str
    call_to_action: Optional[str] = None
    hashtags: list[str] = Field(default_factory=list)
    notes_for_review: list[str] = Field(default_factory=list)


class DraftBundle(BaseModel):
    campaign_name: str
    drafts: list[PlatformDraft] = Field(min_length=1)
    review_notes: list[str] = Field(default_factory=list)


class UpdateCampaignRequest(BaseModel):
    campaign: CampaignPlan


class UpdateDraftRequest(BaseModel):
    content: dict
    change_note: str = "Updated draft"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SignalCraft Multi-Model API",
    version="2.1.0",
    lifespan=lifespan,
)


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            campaign_json TEXT NOT NULL,
            original_brief TEXT NOT NULL,
            provider TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS calendar_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            source_text TEXT NOT NULL,
            provider TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS brand_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            source_text TEXT NOT NULL,
            provider TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS performance_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            report_json TEXT NOT NULL,
            source_text TEXT NOT NULL,
            provider TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS content_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            draft_json TEXT NOT NULL,
            source_text TEXT NOT NULL,
            provider TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS draft_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            content_json TEXT NOT NULL,
            change_note TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(draft_id) REFERENCES content_drafts(id)
        );
        """)

        # Migration for databases created by an older version.
        cols = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(campaigns)"
            ).fetchall()
        }
        if "provider" not in cols:
            conn.execute("ALTER TABLE campaigns ADD COLUMN provider TEXT")

        conn.commit()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def dump(model):
    return model.model_dump(mode="json")


def provider_candidates():
    available = {
        "gemini": bool(os.getenv("GOOGLE_API_KEY")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }
    return [p for p in AI_PROVIDER_ORDER if available.get(p, False)]


def build_llm(provider: str):
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0,
            timeout=90,
            max_retries=0,
        )

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0,
            timeout=90,
            max_retries=0,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
            timeout=90,
            max_retries=0,
        )

    raise ValueError(f"Unknown provider: {provider}")


def run_structured(task: str, source: str, schema, instructions: str):
    candidates = provider_candidates()

    if not candidates:
        raise HTTPException(
            status_code=503,
            detail=(
                "No AI provider is configured. Add a valid API key to .env "
                "and restart the backend."
            ),
        )

    from langchain_core.prompts import ChatPromptTemplate

    failures = []

    system_text = (
        "You are SignalCraft, a precise marketing operations assistant. "
        "Use only facts supported by the supplied source. Never invent factual "
        "metrics, brand claims, dates, budgets, or product details. Represent "
        "unknown fields as null or empty lists. Clearly label recommendations "
        "as recommendations, not facts. "
        + instructions
    )

    # FIX: Escape braces in the system prompt so LangChain does not
    # interpret JSON examples or other braces as template variables.
    system_text = system_text.replace("{", "{{").replace("}", "}}")

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_text),
        ("human", "Task: {task}\n\nSource material:\n{source}"),
    ])

    for provider in candidates:
        try:
            llm = build_llm(provider)
            structured_llm = llm.with_structured_output(schema)

            result = (prompt | structured_llm).invoke({
                "task": task,
                "source": source,
            })

            if isinstance(result, schema):
                return result, provider

            return schema.model_validate(result), provider

        except Exception as exc:
            message = f"{provider}: {type(exc).__name__}: {str(exc)[:700]}"
            failures.append(message)
            logger.exception(
                "Provider %s failed for task %s", provider, task
            )

    raise HTTPException(
        status_code=502,
        detail="All configured AI providers failed. " + " | ".join(failures),
    )


def save_json(
    table,
    name_col,
    name,
    json_col,
    payload,
    source,
    provider,
    created_col="created_at",
    updated_col=None,
):
    stamp = now()

    with connect() as conn:
        if updated_col:
            cursor = conn.execute(
                f"""INSERT INTO {table}
                ({name_col}, {json_col}, source_text, provider,
                 {created_col}, {updated_col})
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    name,
                    json.dumps(payload, ensure_ascii=False),
                    source,
                    provider,
                    stamp,
                    stamp,
                ),
            )
        else:
            cursor = conn.execute(
                f"""INSERT INTO {table}
                ({name_col}, {json_col}, source_text, provider, {created_col})
                VALUES (?, ?, ?, ?, ?)""",
                (
                    name,
                    json.dumps(payload, ensure_ascii=False),
                    source,
                    provider,
                    stamp,
                ),
            )

        conn.commit()
        return cursor.lastrowid, stamp


def list_json(table, json_col, name_key):
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM {table} ORDER BY id DESC"
        ).fetchall()

    output = []
    for row in rows:
        item = dict(row)
        item[name_key] = json.loads(item.pop(json_col))
        item.pop("source_text", None)
        output.append(item)

    return output


@app.get("/health")
def health():
    configured = {
        "gemini": bool(os.getenv("GOOGLE_API_KEY")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }

    return {
        "status": "ok",
        "service": "SignalCraft",
        "provider_order": AI_PROVIDER_ORDER,
        "configured_providers": [
            key for key, value in configured.items() if value
        ],
        "provider_status": configured,
    }


@app.post("/campaigns")
def create_campaign(
    brief: str = Query(..., min_length=10, max_length=30000)
):
    model, provider = run_structured(
        "Extract a campaign plan",
        brief,
        CampaignPlan,
        "Extract campaign name, objective, audience, key message, channels, "
        "dates, budget/currency, CTA, missing information, and a concise summary.",
    )

    payload = dump(model)
    stamp = now()

    with connect() as conn:
        cursor = conn.execute(
            """INSERT INTO campaigns
            (campaign_name, campaign_json, original_brief, provider,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                model.campaign_name,
                json.dumps(payload, ensure_ascii=False),
                brief,
                provider,
                stamp,
                stamp,
            ),
        )
        conn.commit()
        campaign_id = cursor.lastrowid

    return {
        "message": "Campaign extracted and saved",
        "id": campaign_id,
        "campaign": payload,
        "provider": provider,
        "created_at": stamp,
        "updated_at": stamp,
        "original_brief": brief,
    }


@app.get("/campaigns")
def list_campaigns():
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM campaigns ORDER BY id DESC"
        ).fetchall()

    return {
        "campaigns": [
            {
                "id": row["id"],
                "campaign": json.loads(row["campaign_json"]),
                "original_brief": row["original_brief"],
                "provider": row["provider"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    }


@app.put("/campaigns/{cid}")
def update_campaign(cid: int, req: UpdateCampaignRequest):
    payload = dump(req.campaign)
    stamp = now()

    with connect() as conn:
        cursor = conn.execute(
            """UPDATE campaigns
            SET campaign_name=?, campaign_json=?, updated_at=?
            WHERE id=?""",
            (
                req.campaign.campaign_name,
                json.dumps(payload, ensure_ascii=False),
                stamp,
                cid,
            ),
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Campaign not found")

        row = conn.execute(
            "SELECT * FROM campaigns WHERE id=?", (cid,)
        ).fetchone()

    return {
        "id": cid,
        "campaign": payload,
        "provider": row["provider"],
        "created_at": row["created_at"],
        "updated_at": stamp,
        "message": "Campaign updated",
    }


@app.delete("/campaigns/{cid}")
def delete_campaign(cid: int):
    with connect() as conn:
        cursor = conn.execute(
            "DELETE FROM campaigns WHERE id=?", (cid,)
        )
        conn.commit()

    if not cursor.rowcount:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return {"message": "Campaign deleted", "id": cid}


@app.post("/calendar")
def create_calendar(
    source: str = Query(..., min_length=10, max_length=30000),
    count: int = Query(10, ge=1, le=60),
    platforms: str = Query("Instagram,LinkedIn,YouTube,Email"),
):
    task = (
        f"Create {count} practical content calendar entries. "
        f"Preferred platforms: {platforms}. Use dates only if supplied "
        "in source; otherwise leave publish_date null. Return entries with "
        "title, platform, content_type, objective, draft_caption, CTA, "
        "hashtags, and status."
    )

    model, provider = run_structured(
        task,
        source,
        ContentCalendar,
        "Generate a realistic calendar from the stated marketing objective. "
        "Do not fabricate a start date. Make entries varied and usable.",
    )

    payload = dump(model)
    record_id, stamp = save_json(
        "calendar_plans",
        "campaign_name",
        model.campaign_name,
        "plan_json",
        payload,
        source,
        provider,
    )

    return {
        "id": record_id,
        "plan": payload,
        "provider": provider,
        "created_at": stamp,
        "message": "Content calendar generated and saved",
    }


@app.get("/calendar")
def list_calendars():
    return {"plans": list_json("calendar_plans", "plan_json", "plan")}


@app.post("/brand-profiles")
def create_brand_profile(
    source: str = Query(..., min_length=10, max_length=40000)
):
    model, provider = run_structured(
        "Extract a reusable brand profile",
        source,
        BrandProfile,
        "Extract brand identity, industry, products/services, audience, voice, "
        "phrases to use/avoid, differentiators, and visual guidance. "
        "Use missing_information when details are absent.",
    )

    payload = dump(model)
    record_id, stamp = save_json(
        "brand_profiles",
        "brand_name",
        model.brand_name,
        "profile_json",
        payload,
        source,
        provider,
        updated_col="updated_at",
    )

    return {
        "id": record_id,
        "profile": payload,
        "provider": provider,
        "created_at": stamp,
        "updated_at": stamp,
        "message": "Brand profile extracted and saved",
    }


@app.get("/brand-profiles")
def list_brand_profiles():
    return {
        "profiles": list_json(
            "brand_profiles", "profile_json", "profile"
        )
    }


@app.post("/performance-insights")
def create_performance_insights(
    source: str = Query(..., min_length=10, max_length=40000)
):
    model, provider = run_structured(
        "Analyze campaign performance notes",
        source,
        PerformanceInsight,
        "Extract only metrics actually supplied. Each key_metrics item should "
        "contain metric, value, and context when available. Separate observed "
        "facts from recommendations. Tie next actions to evidence and note uncertainty.",
    )

    payload = dump(model)
    title = model.campaign_name or "Campaign performance report"

    record_id, stamp = save_json(
        "performance_reports",
        "title",
        title,
        "report_json",
        payload,
        source,
        provider,
    )

    return {
        "id": record_id,
        "report": payload,
        "provider": provider,
        "created_at": stamp,
        "message": "Performance insights generated and saved",
    }


@app.get("/performance-insights")
def list_performance_insights():
    return {
        "reports": list_json(
            "performance_reports", "report_json", "report"
        )
    }


@app.post("/content-drafts")
def create_content_drafts(
    source: str = Query(..., min_length=10, max_length=30000),
    platforms: str = Query("Instagram,LinkedIn,YouTube"),
):
    task = (
        f"Create platform-specific draft variants for: {platforms}. "
        "Each draft must match its platform and include platform, format, "
        "headline if appropriate, body, CTA, hashtags, and notes_for_review."
    )

    model, provider = run_structured(
        task,
        source,
        DraftBundle,
        "Create distinct drafts from one approved campaign brief. "
        "Do not add unverified claims or fake testimonials. Use placeholders "
        "or review notes when details need approval.",
    )

    payload = dump(model)
    record_id, stamp = save_json(
        "content_drafts",
        "campaign_name",
        model.campaign_name,
        "draft_json",
        payload,
        source,
        provider,
        updated_col="updated_at",
    )

    with connect() as conn:
        conn.execute(
            """INSERT INTO draft_versions
            (draft_id, version_number, content_json, change_note, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (
                record_id,
                1,
                json.dumps(payload, ensure_ascii=False),
                "Initial generated version",
                stamp,
            ),
        )
        conn.commit()

    return {
        "id": record_id,
        "draft_bundle": payload,
        "provider": provider,
        "version": 1,
        "created_at": stamp,
        "updated_at": stamp,
        "message": "Platform drafts generated and saved",
    }


@app.get("/content-drafts")
def list_content_drafts():
    return {
        "drafts": list_json(
            "content_drafts", "draft_json", "draft_bundle"
        )
    }


@app.put("/content-drafts/{draft_id}")
def update_content_drafts(
    draft_id: int, req: UpdateDraftRequest
):
    stamp = now()

    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM content_drafts WHERE id=?", (draft_id,)
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=404, detail="Draft bundle not found"
            )

        last_version = conn.execute(
            "SELECT COALESCE(MAX(version_number), 0) "
            "FROM draft_versions WHERE draft_id=?",
            (draft_id,),
        ).fetchone()[0]

        version = last_version + 1
        raw = json.dumps(req.content, ensure_ascii=False)

        conn.execute(
            "UPDATE content_drafts SET draft_json=?, updated_at=? WHERE id=?",
            (raw, stamp, draft_id),
        )
        conn.execute(
            """INSERT INTO draft_versions
            (draft_id, version_number, content_json, change_note, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (draft_id, version, raw, req.change_note, stamp),
        )
        conn.commit()

    return {
        "id": draft_id,
        "version": version,
        "updated_at": stamp,
        "message": "Draft updated and version saved",
    }


@app.get("/content-drafts/{draft_id}/versions")
def draft_versions(draft_id: int):
    with connect() as conn:
        exists = conn.execute(
            "SELECT id FROM content_drafts WHERE id=?", (draft_id,)
        ).fetchone()

        if not exists:
            raise HTTPException(
                status_code=404, detail="Draft bundle not found"
            )

        rows = conn.execute(
            """SELECT * FROM draft_versions
            WHERE draft_id=? ORDER BY version_number DESC""",
            (draft_id,),
        ).fetchall()

    return {
        "versions": [
            {
                "id": row["id"],
                "version": row["version_number"],
                "content": json.loads(row["content_json"]),
                "change_note": row["change_note"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    }
