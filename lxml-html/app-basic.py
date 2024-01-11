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


def head(title: str):
    return e.head(
        e.meta(charset="utf-8"),
        e.meta(name="viewport", content="width=device-width, initial-scale=1"),
        e.title(title),
    )


def list_items(items: list[str]):
    return e.ul(*[e.li(item) for item in items])


def index(items: list[str]):
    return e.html(
        # generate <head> element by calling a python function
        head("Home"),
        e.body(
            e.h1("Hello, world!"),
            list_items(items),
        ),
    )


@app.get("/", response_class=HTMLResponse)
def get():
    items = [str(random.randint(0, 100)) for _ in range(10)]
    tree = index(items)
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
