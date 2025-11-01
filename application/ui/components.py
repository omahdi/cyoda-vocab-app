from fasthtml.common import *


def base_layout(title: str, *content):
    """Base HTML layout with HTMX and Pico CSS"""
    return Html(
        Head(
            Title(title),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css",
            ),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            Nav(
                Ul(Li(Strong("Vocabulary App"))),
                Ul(Li(A("Admin", href="/ui")), Li(A("API Docs", href="/docs"))),
            ),
            Main(*content, cls="container"),
        ),
    )


def vocabulary_form():
    """Form for creating vocabulary items"""
    return Article(
        H2("Create Vocabulary Item"),
        Form(
            Input(
                type="text",
                name="front",
                placeholder="Front (e.g., hello)",
                required=True,
            ),
            Input(
                type="text", name="back", placeholder="Back (e.g., hola)", required=True
            ),
            Input(type="text", name="comment", placeholder="Comment (optional)"),
            Input(type="text", name="lesson", placeholder="Lesson (optional)"),
            Button("Create", type="submit"),
            hx_post="/ui/items",
            hx_target="#items-tbody",
            hx_swap="afterbegin",
        ),
    )


def vocabulary_table_shell():
    """Empty table structure that HTMX will populate"""
    return Article(
        H2("Vocabulary Items"),
        Table(
            Thead(Tr(Th("Front"), Th("Back"), Th("Comment"), Th("Lesson"), Th("Actions"))),
            Tbody(
                id="items-tbody",
                hx_get="/ui/items",
                hx_trigger="load",
                hx_swap="innerHTML",
            ),
        ),
    )


def vocabulary_row(item: dict):
    """Single vocabulary item row"""
    return Tr(
        Td(item.get("front", "")),
        Td(item.get("back", "")),
        Td(item.get("comment", "—")),
        Td(item.get("lesson", "—")),
        Td(
            Button(
                "Delete",
                hx_delete=f"/ui/items/{item.get('id')}",
                hx_target="closest tr",
                hx_swap="outerHTML swap:1s",
                hx_confirm="Delete this item?",
            )
        ),
    )


def share_form():
    """Form for creating share links"""
    return Article(
        H2("Create Share Link"),
        Form(
            Input(
                type="text",
                name="token",
                placeholder="Token (e.g., my-vocab-2025)",
                required=True,
            ),
            Input(
                type="text",
                name="label",
                placeholder="Label (e.g., Spanish Vocabulary)",
            ),
            Button("Create Share Link", type="submit"),
            hx_post="/ui/share",
            hx_target="#share-result",
            hx_swap="innerHTML",
        ),
        Div(id="share-result"),
    )


def share_result(token: str, url: str, label: str):
    """Display created share link"""
    return Article(
        H3("✅ Share Link Created"),
        P(Strong("Token: "), token),
        P(Strong("Label: "), label or "—"),
        P(Strong("URL: "), A(url, href=url, target="_blank")),
    )


def public_viewer_page(token: str, data: dict):
    """Public viewer page for shared vocabulary"""
    items = data.get("items", [])
    share_info = data.get("share_info", {})

    return base_layout(
        f"Shared Vocabulary - {data.get('label', token)}",
        Article(
            H1(data.get("label") or f"Shared Vocabulary ({token})"),
            P(f"Total items: {data.get('total', 0)}"),
            P(
                Small(
                    f"Created: {share_info.get('created_at', 'Unknown')} | "
                    f"Views: {share_info.get('visit_count', 0)}"
                )
            ),
        ),
        Article(
            Table(
                Thead(Tr(Th("Front"), Th("Back"), Th("Comment"), Th("Lesson"))),
                Tbody(*[public_vocabulary_row(item) for item in items]),
            )
        ),
    )


def public_vocabulary_row(item: dict):
    """Read-only vocabulary item row for public viewer"""
    return Tr(
        Td(item.get("front", "")),
        Td(item.get("back", "")),
        Td(item.get("comment", "—")),
        Td(item.get("lesson", "—")),
    )
