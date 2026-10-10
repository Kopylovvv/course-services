from fastapi import FastAPI


def create_app(settings, routers, **params):
    app_params = {**settings.app.model_dump(), **params}
    app = FastAPI(**app_params)
    for router in routers:
        app.include_router(router)
    return app
