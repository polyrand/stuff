"""
This uses DaisyUI and TailwindCSS for styling. This is not production ready, it
loads the CSS from CDN.
"""

import random

# import MappingProxyType for frozen dict
from types import MappingProxyType

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from lxml.html import HtmlElement
from lxml.html import tostring
from lxml.html.builder import E as e

app = FastAPI()


State = dict | MappingProxyType


def replace_attr_name(name: str) -> str:
    if name == "_class":
        return "class"
    elif name == "_for":
        return "for"
    return name


def ATTR(**kwargs):
    # Use str() to convert values to string. This way we can set boolean
    # attributes using True instead of "true".
    return {replace_attr_name(k): str(v) for k, v in kwargs.items()}


def s(tree: HtmlElement) -> str:
    """
    Serialize LXML tree to unicode string. Using DOCTYPE html.
    """
    return tostring(tree, encoding="unicode", doctype="<!DOCTYPE html>")


def head(state: State):
    return e.head(
        e.meta(charset="utf-8"),
        e.title(state.get("title", "Home")),
        e.meta(name="viewport", content="width=device-width, initial-scale=1"),
        e.meta(name="description", content="Welcome."),
        e.meta(name="author", content="@polyrand"),
        e.link(
            rel="stylesheet",
            type="text/css",
            href="https://cdn.jsdelivr.net/npm/daisyui@4.0.5/dist/full.min.css",
        ),
        e.script(
            src="https://cdn.tailwindcss.com",
        ),
    )


def list_items(state: State):
    return e.ul(*[e.li(item) for item in state["items"]])


def base(*children: HtmlElement, state: State):
    return e.html(
        ATTR(lang="en"),
        head(state),
        e.body(
            e.main(ATTR(id="main", _class="container mx-auto"), *children),
        ),
    )


def login(state: State):
    return e.article(
        ATTR(**{"aria-label": "log-in form"}),
        e.p(
            e.strong("Wrong credentials!")
            if state.get("error")
            else "You will receive an email with a link to log in."
        ),
        e.form(
            e.label("Email", _for="email"),
            e.input(
                ATTR(
                    placeholder="Your email",
                    type="email",
                    name="email",
                    required=True,
                )
            ),
            e.button(ATTR(_class="btn"), "Log In"),
            action="/login",
            method="post",
        ),
    )


def view_index(state: State):
    return base(
        e.section(
            e.h1("ML tooling"),
            e.p("This is some text."),
        ),
        list_items(state),
        login(state),
        state=state,
    )


@app.get("/", response_class=HTMLResponse)
def idx():
    items = [str(random.randint(0, 100)) for _ in range(10)]
    state = {
        "title": "Some title",
        "items": items,
    }
    tree = view_index(MappingProxyType(state))
    html = s(tree)
    return html


@app.get("/error", response_class=HTMLResponse)
def idx2():
    items = [str(random.randint(0, 100)) for _ in range(10)]
    state = {"title": "Some title", "items": items, "error": True}
    tree = view_index(MappingProxyType(state))
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
