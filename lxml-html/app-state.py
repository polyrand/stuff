import random

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from lxml.html import HtmlElement
from lxml.html import tostring
from lxml.html.builder import E as e

app = FastAPI()


def s(tree: HtmlElement) -> str:
    """
    Serialize LXML tree to unicode string. Using DOCTYPE html.
    """
    return tostring(tree, encoding="unicode", doctype="<!DOCTYPE html>")


def head(state: dict):
    return e.head(
        e.meta(charset="utf-8"),
        e.title(state.get("title", "Home")),
    )


def list_items(state: dict):
    return e.ul(*[e.li(item) for item in state["items"]])


def index(state: dict):
    return e.html(
        head(state),
        e.body(
            e.h1("Hello, world!"),
            list_items(state),
        ),
    )


@app.get("/", response_class=HTMLResponse)
def get():
    items = [str(random.randint(0, 100)) for _ in range(10)]
    state = {
        "title": "Some title",
        "items": items,
    }
    tree = index(state)
    html = s(tree)
    return html


if __name__ == "__main__":
    uvicorn.run(
        f'{__file__.split("/")[-1].replace(".py", "")}:app',
        host="127.0.0.1",
        port=8000,
        reload=True,
        workers=1,
    )
