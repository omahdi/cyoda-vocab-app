import httpx
from quart import Blueprint

from application.ui.components import (
    base_layout,
    public_viewer_page,
    share_form,
    share_result,
    vocabulary_form,
    vocabulary_row,
    vocabulary_table_shell,
)
from fasthtml.common import A, Article, H1, P

ui_bp = Blueprint("ui", __name__)

BASE_API_URL = "http://127.0.0.1:8000/api"


async def call_api(method: str, path: str, json_data: dict = None):
    """Helper to call internal API endpoints"""
    async with httpx.AsyncClient() as client:
        url = f"{BASE_API_URL}{path}"
        response = await client.request(method, url, json=json_data)
        response.raise_for_status()
        return response.json()


@ui_bp.route("/ui", methods=["GET"])
async def admin_page():
    """Admin interface - main page"""
    page = base_layout(
        "Vocabulary Admin",
        Article(H1("Vocabulary Management")),
        vocabulary_form(),
        vocabulary_table_shell(),
        share_form(),
    )
    return str(page)


@ui_bp.route("/ui/items", methods=["GET"])
async def get_items():
    """HTMX endpoint to fetch all vocabulary items"""
    try:
        data = await call_api("GET", "/vocabulary-items")
        items = data.get("entities", [])
        rows = [vocabulary_row(item) for item in items]
        return "".join(str(row) for row in rows)
    except Exception as e:
        return f"<tr><td colspan='5'>Error loading items: {str(e)}</td></tr>"


@ui_bp.route("/ui/items", methods=["POST"])
async def create_item():
    """HTMX endpoint to create a vocabulary item"""
    from quart import request

    try:
        form_data = await request.form
        item_data = {
            "front": form_data.get("front"),
            "back": form_data.get("back"),
            "comment": form_data.get("comment") or None,
            "lesson": form_data.get("lesson") or None,
        }

        result = await call_api("POST", "/vocabulary-items", json_data=item_data)
        return str(vocabulary_row(result))

    except Exception as e:
        return f"<tr><td colspan='5'>Error creating item: {str(e)}</td></tr>"


@ui_bp.route("/ui/items/<item_id>", methods=["DELETE"])
async def delete_item(item_id: str):
    """HTMX endpoint to delete a vocabulary item"""
    try:
        await call_api("DELETE", f"/vocabulary-items/{item_id}")
        return ""
    except Exception as e:
        return f"<div>Error deleting item: {str(e)}</div>"


@ui_bp.route("/ui/share", methods=["POST"])
async def create_share():
    """HTMX endpoint to create a share link"""
    from quart import request

    try:
        form_data = await request.form
        share_data = {
            "token": form_data.get("token"),
            "label": form_data.get("label") or None,
        }

        result = await call_api("POST", "/share-links", json_data=share_data)

        token = result.get("token")
        full_url = f"http://localhost:8000/s/{token}"

        return str(share_result(token, full_url, result.get("label", "")))

    except Exception as e:
        return f"<div>Error creating share link: {str(e)}</div>"


@ui_bp.route("/s/<token>", methods=["GET"])
async def public_viewer(token: str):
    """Public viewer for shared vocabulary"""
    try:
        data = await call_api("GET", f"/shared/{token}")
        page = public_viewer_page(token, data)
        return str(page)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return (
                str(
                    base_layout(
                        "Share Not Found",
                        Article(
                            H1("Share Link Not Found"),
                            P(f"No shared vocabulary found for token: {token}"),
                            A("Go to Admin", href="/ui"),
                        ),
                    )
                ),
                404,
            )
        raise
    except Exception as e:
        return (
            str(
                base_layout(
                    "Error",
                    Article(
                        H1("Error Loading Shared Vocabulary"),
                        P(str(e)),
                        A("Go to Admin", href="/ui"),
                    ),
                )
            ),
            500,
        )
