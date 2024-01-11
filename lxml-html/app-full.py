import random

# import MappingProxyType for "frozen dict"
from types import MappingProxyType

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from lxml.html import HtmlElement
from lxml.html import tostring
from lxml.html.builder import E as e

app = FastAPI()

# Type alias. State can be a dict or a MappingProxyType.
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


def base(*children: HtmlElement, state: State):
    """
    Base HTML for all pages.
    """
    return e.html(
        ATTR(lang="en"),
        head(state),
        e.body(
            e.main(ATTR(id="main", _class="container"), *children),
        ),
    )


def head(state: State):
    return e.head(
        e.meta(charset="utf-8"),
        e.title(state.get("title", "Home")),
        e.meta(name="viewport", content="width=device-width, initial-scale=1"),
        e.meta(name="description", content="Welcome."),
        e.meta(name="author", content="@polyrand"),
        e.link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css",
        ),
    )


def login_form(state: State):
    return e.article(
        ATTR(**{"aria-label": "log-in form"}),
        e.p(
            e.strong(ATTR(style="color: red"), "Wrong credentials!")
            if state.get("error")
            else f"{state.get('user', 'You')} will receive an email with a link to log in."
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
            e.button("Log In"),
            action="/login",
            method="post",
        ),
    )


def view_index(state: State):
    return base(
        e.section(
            e.h1("Page built using lxml"),
            e.p("This is some text."),
        ),
        list_items(state),
        login_form(state),
        state=state,
    )


def list_items(state: State):
    return e.ul(*[e.li(item) for item in state["items"]])


@app.get("/", response_class=HTMLResponse)
def idx(error: bool = False):
    items = [str(random.randint(0, 100)) for _ in range(4)]
    state = {
        "title": "Some title",
        "items": items,
        "user": "@polyrand",
    }
    if error:
        state["error"] = True
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
