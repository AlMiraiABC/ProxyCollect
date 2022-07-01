from aiohttp import web
from web.query import app as query_app

routes = web.RouteTableDef()

app = web.Application()
app.add_routes(routes)
app.add_subapp('/query', query_app)
if __name__ == '__main__':
    web.run_app(app)
