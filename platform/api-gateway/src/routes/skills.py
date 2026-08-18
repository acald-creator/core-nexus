"""Skills routes — list and content retrieval from MinIO."""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

router = APIRouter()

SKILLS_PREFIX = "skills/"


@router.get("/skills")
async def list_skills(
    request: Request,
    search: str | None = None,
    tag: str | None = None,
    domain: str | None = None,
):
    """List skills from MinIO with optional filtering."""
    try:
        objects = request.app.state.minio_client.list_objects(prefix=SKILLS_PREFIX)
    except Exception:
        raise HTTPException(status_code=502, detail="MinIO unavailable")

    skills = []
    for obj in objects:
        if not obj["name"].endswith(".md") or obj["name"] == "README.md":
            continue

        name = obj["name"].replace(".md", "")
        # Parse basic metadata from filename
        skill_entry = {
            "id": name,
            "name": name,
            "description": "",
            "tags": _extract_domain_tags(name),
            "domain": _infer_domain(name),
            "contentUrl": f"/api/v1/skills/{name}/content",
        }

        # Apply filters
        if search and search.lower() not in name.lower():
            continue
        if domain and skill_entry["domain"] != domain:
            continue
        if tag and tag not in skill_entry["tags"]:
            continue

        skills.append(skill_entry)

    return skills


@router.get("/skills/{skill_id}/content")
async def get_skill_content(skill_id: str, request: Request):
    """Retrieve raw markdown content of a skill."""
    key = f"{SKILLS_PREFIX}{skill_id}.md"
    try:
        content = request.app.state.minio_client.get_object_content(key)
        return PlainTextResponse(content, media_type="text/markdown")
    except Exception:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")


def _extract_domain_tags(name: str) -> list[str]:
    """Extract tags from skill filename convention."""
    parts = name.split("-")
    if parts:
        return [parts[0]]
    return []


def _infer_domain(name: str) -> str:
    """Infer domain from skill name prefix."""
    if name.startswith("red-team"):
        return "red-team"
    elif name.startswith("blue-team"):
        return "blue-team"
    elif name.startswith("architecture") or name.startswith("deployment"):
        return "infrastructure"
    return "general"
