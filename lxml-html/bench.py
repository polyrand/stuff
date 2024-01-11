import random
from functools import lru_cache

import jinja2
from lxml.html import HtmlElement
from lxml.html import tostring
from lxml.html.builder import E as e

items = [str(random.randint(0, 100)) for _ in range(100)]

jinja_template = jinja2.Template(
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Welcome.">
    <meta name="author" content="@polyrand">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <main id="main" class="container">
    <ol>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
    </ol>
    </main>
</body>
</html>
"""
)


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


def generate_jinja(items: list) -> str:
    return jinja_template.render(title="Home", items=items)


def generate_jinja_recreate_template(items: list) -> str:
    return jinja2.Template(
        """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Welcome.">
    <meta name="author" content="@polyrand">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <main id="main" class="container">
    <ol>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
    </ol>
    </main>
</body>
</html>
"""
    ).render(title="Home", items=items)


def generate_lxml(items: list) -> str:
    return s(
        e.html(
            ATTR(lang="en"),
            e.head(
                e.meta(charset="utf-8"),
                e.title("Home"),
                e.meta(name="viewport", content="width=device-width, initial-scale=1"),
                e.meta(name="description", content="Welcome."),
                e.meta(name="author", content="@polyrand"),
                e.link(
                    rel="stylesheet",
                    href="/static/style.css",
                ),
            ),
            e.body(
                e.main(
                    ATTR(id="main", _class="container"),
                    e.ol(*[e.li(item) for item in items]),
                ),
            ),
        )
    )


@lru_cache(maxsize=10000)
def mk(el: str, *args, **kwargs) -> HtmlElement:
    # mkf is "maker function". i.e: the function that would
    # generate the element `el`
    # e.li  ->  li_maker = getattr(e, "li")
    mkf = getattr(e, el)
    return mkf(*args, **kwargs)


# Generate component using LXML cached builder.
def generate_lxml_cache(items: list) -> str:
    return s(
        mk(
            "html",
            mk(
                "head",
                mk("meta", charset="utf-8"),
                mk("title", "Home"),
                mk(
                    "meta",
                    name="viewport",
                    content="width=device-width, initial-scale=1",
                ),
                mk("meta", name="description", content="Welcome."),
                mk("meta", name="author", content="@polyrand"),
                mk(
                    "link",
                    rel="stylesheet",
                    href="/static/style.css",
                ),
            ),
            mk(
                "body",
                mk(
                    "main",
                    mk("ol", *[mk("li", item) for item in items]),
                    id="main",
                    _class="container",
                ),
            ),
            lang="en",
        )
    )


# Run this inside IPython
"""
%run bench.py

print("Jinja")
%timeit generate_jinja(items)

print("Jinja recreate template")
%timeit generate_jinja_recreate_template(items)

print("LXML")
%timeit generate_lxml(items)

print("LXML cached builder")
%timeit generate_lxml_cache(items)
"""
