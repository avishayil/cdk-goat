from aiohttp.web import Application
from aiohttp_jinja2 import setup as setup_jinja
from jinja2.loaders import PackageLoader
from sqli.middlewares import error_middleware, session_middleware
from sqli.services.db import setup_database
from sqli.utils.jinja2 import auth_user_processor, csrf_processor

from .routes import setup_routes


def init():
    app = Application(
        debug=True,
        middlewares=[
            # csrf_middleware,
            session_middleware,
            error_middleware,
        ],
    )

    setup_jinja(
        app,
        loader=PackageLoader("sqli", "templates"),
        context_processors=[csrf_processor, auth_user_processor],
        autoescape=False,
    )
    setup_database(app)
    setup_routes(app)

    return app
