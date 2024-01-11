import random
from functools import partial

# import MappingProxyType for frozen dict
from types import MappingProxyType

import lxml.etree as ET
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from lxml.html import HtmlElement
from lxml.html import html_parser
from lxml.html import tostring
from markupsafe import escape

_QName = ET.QName


class ElementMaker:
    """Element generator factory.

    Unlike the ordinary Element factory, the E factory allows you to pass in
    more than just a tag and some optional attributes; you can also pass in
    text and other elements.  The text is added as either text or tail
    attributes, and elements are inserted at the right spot.  Some small
    examples::

        >>> from lxml import etree as ET
        >>> from lxml.builder import E

        >>> ET.tostring(E("tag"))
        '<tag/>'
        >>> ET.tostring(E("tag", "text"))
        '<tag>text</tag>'
        >>> ET.tostring(E("tag", "text", key="value"))
        '<tag key="value">text</tag>'
        >>> ET.tostring(E("tag", E("subtag", "text"), "tail"))
        '<tag><subtag>text</subtag>tail</tag>'

    For simple tags, the factory also allows you to write ``E.tag(...)`` instead
    of ``E('tag', ...)``::

        >>> ET.tostring(E.tag())
        '<tag/>'
        >>> ET.tostring(E.tag("text"))
        '<tag>text</tag>'
        >>> ET.tostring(E.tag(E.subtag("text"), "tail"))
        '<tag><subtag>text</subtag>tail</tag>'

    Here's a somewhat larger example; this shows how to generate HTML
    documents, using a mix of prepared factory functions for inline elements,
    nested ``E.tag`` calls, and embedded XHTML fragments::

        # some common inline elements
        A = E.a
        I = E.i
        B = E.b

        def CLASS(v):
            # helper function, 'class' is a reserved word
            return {'class': v}

        page = (
            E.html(
                E.head(
                    E.title("This is a sample document")
                ),
                E.body(
                    E.h1("Hello!", CLASS("title")),
                    E.p("This is a paragraph with ", B("bold"), " text in it!"),
                    E.p("This is another paragraph, with a ",
                        A("link", href="http://www.python.org"), "."),
                    E.p("Here are some reserved characters: <spam&egg>."),
                    ET.XML("<p>And finally, here is an embedded XHTML fragment.</p>"),
                )
            )
        )

        print ET.tostring(page)

    Here's a prettyprinted version of the output from the above script::

        <html>
          <head>
            <title>This is a sample document</title>
          </head>
          <body>
            <h1 class="title">Hello!</h1>
            <p>This is a paragraph with <b>bold</b> text in it!</p>
            <p>This is another paragraph, with <a href="http://www.python.org">link</a>.</p>
            <p>Here are some reserved characters: &lt;spam&amp;egg&gt;.</p>
            <p>And finally, here is an embedded XHTML fragment.</p>
          </body>
        </html>

    For namespace support, you can pass a namespace map (``nsmap``)
    and/or a specific target ``namespace`` to the ElementMaker class::

        >>> E = ElementMaker(namespace="http://my.ns/")
        >>> print(ET.tostring( E.test ))
        <test xmlns="http://my.ns/"/>

        >>> E = ElementMaker(namespace="http://my.ns/", nsmap={'p':'http://my.ns/'})
        >>> print(ET.tostring( E.test ))
        <p:test xmlns:p="http://my.ns/"/>
    """

    def __init__(self, typemap=None, namespace=None, nsmap=None, makeelement=None):
        self._namespace = "{" + namespace + "}" if namespace is not None else None
        self._nsmap = dict(nsmap) if nsmap else None

        assert makeelement is None or callable(makeelement)
        self._makeelement = makeelement if makeelement is not None else ET.Element

        # initialize the default type map functions for this element factory
        typemap = dict(typemap) if typemap else {}

        def add_text(elem, item):
            try:
                last_child = elem[-1]
            except IndexError:
                elem.text = (elem.text or "") + item
            else:
                last_child.tail = (last_child.tail or "") + item

        def add_cdata(elem, cdata):
            if elem.text:
                raise ValueError(
                    "Can't add a CDATA section. Element already has some text: %r"
                    % elem.text
                )
            elem.text = cdata

        if str not in typemap:
            typemap[str] = add_text
        if ET.CDATA not in typemap:
            typemap[ET.CDATA] = add_cdata

        def add_dict(elem, item):
            attrib = elem.attrib
            for k, v in item.items():
                if isinstance(v, str):
                    attrib[k] = v
                else:
                    attrib[k] = typemap[type(v)](None, v)

        if dict not in typemap:
            typemap[dict] = add_dict

        self._typemap = typemap

    def __call__(self, tag, *children, **attrib):
        typemap = self._typemap

        # We'll usually get a 'str', and the compiled type check is very fast.
        if not isinstance(tag, str) and isinstance(tag, _QName):
            # A QName is explicitly qualified, do not look at self._namespace.
            tag = tag.text
        elif self._namespace is not None and tag[0] != "{":
            tag = self._namespace + tag
        elem = self._makeelement(tag, nsmap=self._nsmap)
        if attrib:
            typemap[dict](elem, attrib)

        for item in children:
            if callable(item):
                item = item()
            # escape all the strings by default
            if isinstance(item, str):
                item = escape(item)
            print(f"item1: {item}")
            t = typemap.get(type(item))
            print(f"t1: {t}")
            if t is None:
                if ET.iselement(item):
                    elem.append(item)
                    continue
                for basetype in type(item).__mro__:
                    # See if the typemap knows of any of this type's bases.
                    t = typemap.get(basetype)
                    if t is not None:
                        break
                else:
                    raise TypeError(
                        "bad argument type: %s(%r)" % (type(item).__name__, item)
                    )

            v = t(elem, item)
            print(f"item: {item}, type: {type(item)}, t: {t}, v: {v}")
            if v:
                typemap.get(type(v))(elem, v)

        return elem

    def __getattr__(self, tag):
        return partial(self, tag)


e = ElementMaker(makeelement=html_parser.makeelement)

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
            href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css",
        ),
    )


def list_items(state: State):
    return e.ul(*[e.li(item) for item in state["items"]])


def base(*children: HtmlElement, state: State):
    return e.html(
        ATTR(lang="en"),
        head(state),
        e.body(
            e.main(ATTR(id="main", _class="container"), *children),
        ),
    )


def login(state: State):
    return e.article(
        ATTR(**{"aria-label": "log-in form"}),
        e.p(
            e.strong("Wrong credentials!")
            if state.get("error")
            else f"You {state.get('user')} will receive an email with a link to <script>alert('')</script> log in."
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
            e.button("<script>alert('')</script>"),
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
        "user": "<script>alert('')</script>",
    }
    tree = view_index(state)
    html = s(tree)
    return html


@app.get("/error", response_class=HTMLResponse)
def idx2():
    items = [str(random.randint(0, 100)) for _ in range(10)]
    state = {"title": "Some title", "items": items, "error": True}
    tree = view_index(state)
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
