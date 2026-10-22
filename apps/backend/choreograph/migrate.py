from pathlib import Path

from alembic import command
from alembic.config import Config


def migrate(engine, target="head"):
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        command.upgrade(config, target)


def downgrade(engine, target):
    config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    with engine.begin() as connection:
        config.attributes['connection'] = connection
        command.downgrade(config, target)


def main():
    from .db import build_engine
    from .settings import load_local
    engine = build_engine(load_local())
    try:
        migrate(engine)
        print('Choreograph migrations applied to the explicitly configured local database.')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
