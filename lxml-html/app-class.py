import random

# import MappingProxyType for frozen dict
from types import MappingProxyType

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from lxml.html import HtmlElement
from lxml.html import tostring
from lxml.html.builder import E as e

# jinaj2 doesn't autoescape
# https://jinja.palletsprojects.com/en/3.1.x/templates/#html-escaping
# from markupsafe import escape


def gen_par(text: str) -> HtmlElement:
    # generate a <p> element with an <a> element inside
    return e.p(
        "goo",
        e.a(
            text,
            href="https://example.com",
            title="Example",
            target="_blank",
            rel="noopener",
        ),
        "bar",
    )


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


class Views:
    def __init__(self, state: State):
        self.state = state

    def base(self, *children: HtmlElement):
        return e.html(
            ATTR(lang="en"),
            self.head(),
            e.body(
                e.main(ATTR(id="main", _class="container"), *children),
            ),
            # e.script(""),
        )

    def head(self):
        return e.head(
            e.meta(charset="utf-8"),
            e.title(self.state.get("title", "Home")),
            e.meta(name="viewport", content="width=device-width, initial-scale=1"),
            e.meta(name="description", content="Welcome."),
            e.meta(name="author", content="@polyrand"),
            e.link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css",
            ),
        )

    def login(self):
        return e.article(
            ATTR(**{"aria-label": "log-in form"}),
            e.p(
                e.strong(ATTR(style="color: red"), "Wrong credentials!")
                if self.state.get("error")
                else f"{self.state.get('user', 'You')} will receive an email with a link to log in."
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

    def index(self):
        return self.base(
            e.section(
                e.h1("ML tooling"),
                e.p("This is some text."),
            ),
            self.list_items(),
            self.login(),
        )

    def list_items(self):
        return e.ul(*[e.li(item) for item in self.state["items"]])


@app.get("/", response_class=HTMLResponse)
def idx():
    items = [str(random.randint(0, 100)) for _ in range(10)]
    state = {
        "title": "Some title",
        "items": items,
        "user": "Ricardo",
    }
    views = Views(MappingProxyType(state))
    html = s(views.index())
    return html


@app.get("/error", response_class=HTMLResponse)
def idx2():
    items = [str(random.randint(0, 100)) for _ in range(10)]
    state = {"title": "Some title", "items": items, "error": True}
    views = Views(MappingProxyType(state))
    html = s(views.index())
    return html


if __name__ == "__main__":
    uvicorn.run(
        f'{__file__.split("/")[-1].replace(".py", "")}:app',
        host="127.0.0.1",
        port=8000,
        reload=True,
        workers=1,
    )
