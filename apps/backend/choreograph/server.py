def main():
    import uvicorn

    from .api import create_app
    from .composition import compose_ai
    from .crm_composition import compose_crm
    from .db import build_engine
    from .settings import load_local
    settings = load_local()
    engine = build_engine(settings)
    runtime = None
    crm_runtime = None
    try:
        runtime = compose_ai(settings, engine)
        crm_runtime = compose_crm(settings,engine)
        app = create_app(settings, engine, ai_runtime=runtime,crm_provider=crm_runtime)
        uvicorn.run(app, host="127.0.0.1", port=45861, access_log=False, log_level="critical")
    finally:
        try:
            try:
                if crm_runtime is not None:crm_runtime.close()
            finally:
                if runtime is not None:runtime.close()
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
