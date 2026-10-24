import sys
from contextlib import contextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from test_ai_config import live_values

from choreograph import composition, release, runner, server
from choreograph.settings import Settings


class Engine:
    def __init__(self):
        self.disposed = False
        self.queries = []

    @contextmanager
    def connect(self):
        yield self

    def execute(self, statement):
        self.queries.append(str(statement))

    def dispose(self):
        self.disposed = True


class Runtime:
    def __init__(self, *, close_error=False):
        self.closes = 0
        self.scopes = []
        self.close_error = close_error
        self.scoped = SimpleNamespace(spec=object(), embedder=object(), tokenizer=object())

    def for_scope(self, scope):
        self.scopes.append(scope)
        return self.scoped

    def close(self):
        self.closes += 1
        if self.close_error:
            raise RuntimeError('synthetic-close-failure')


@pytest.mark.parametrize('command_key', [None, 'not-a-uuid'])
def test_live_preparation_requires_operator_command_before_client_creation(monkeypatch, command_key):
    engine = Engine()
    monkeypatch.setattr(release, 'load_environment', lambda: Settings.parse(live_values()))
    monkeypatch.setattr(release, 'build_engine', lambda _: engine)
    def denied(*args, **kwargs):
        raise AssertionError('Unidentified preparation must not compose paid clients')
    monkeypatch.setattr(release, 'compose_ai', denied)
    monkeypatch.setattr(sys, 'argv', ['release', 'prepare-knowledge'] +
                        (['--command-key', command_key] if command_key else []))
    with pytest.raises(ValueError, match='EXPLICIT_PREPARATION_COMMAND_KEY_REQUIRED'):
        release.main()
    assert engine.disposed


def test_live_preparation_binds_explicit_scope_and_closes_owned_runtime(monkeypatch, capsys):
    from choreograph import knowledge

    engine, runtime, command = Engine(), Runtime(), str(uuid4())
    monkeypatch.setattr(release, 'load_environment', lambda: Settings.parse(live_values()))
    monkeypatch.setattr(release, 'build_engine', lambda _: engine)
    monkeypatch.setattr(release, 'compose_ai', lambda *_: runtime)
    calls = []
    def prepare(engine_arg, now, **kwargs):
        calls.append((engine_arg, kwargs))
        return {'prepared': 6}
    monkeypatch.setattr(knowledge, 'prepare_pack', prepare)
    monkeypatch.setattr(sys, 'argv', ['release', 'prepare-knowledge', '--command-key', command])
    release.main()
    assert engine.queries == ['SELECT 1'] and engine.disposed
    assert runtime.closes == 1
    assert runtime.scopes[0].workspace_id is None and runtime.scopes[0].generation == 0
    assert runtime.scopes[0].command_key == command
    assert calls == [(engine, {'spec': runtime.scoped.spec, 'embedder': runtime.scoped.embedder,
                              'tokenizer': runtime.scoped.tokenizer})]
    assert capsys.readouterr().out == '{"code":"KNOWLEDGE_PREPARED","count":6}\n'


def test_server_startup_failure_still_disposes_engine_if_runtime_close_fails(monkeypatch):
    import choreograph.api
    import choreograph.db
    import choreograph.settings

    engine, runtime = Engine(), Runtime(close_error=True)
    monkeypatch.setattr(choreograph.settings, 'load_local', lambda: object())
    monkeypatch.setattr(choreograph.db, 'build_engine', lambda _: engine)
    monkeypatch.setattr(composition, 'compose_ai', lambda *_: runtime)
    def failed_app(*args, **kwargs):
        assert kwargs['ai_runtime'] is runtime
        raise ValueError('synthetic-startup-failure')
    monkeypatch.setattr(choreograph.api, 'create_app', failed_app)
    with pytest.raises(RuntimeError, match='synthetic-close-failure'):
        server.main()
    assert runtime.closes == 1 and engine.disposed


def test_once_runner_composes_and_closes_without_listener_or_provider_calls(monkeypatch, tmp_path):
    engine, runtime = Engine(), Runtime()
    settings = Settings.parse({**live_values(), 'FAKE_MODE':'true'}, testing=True)
    monkeypatch.setattr(runner, 'load_local', lambda: settings)
    monkeypatch.setattr(runner, 'build_engine', lambda _: engine)
    monkeypatch.setattr(runner, 'compose_ai', lambda *_: runtime)
    monkeypatch.setattr(runner, '__file__', str(tmp_path / 'apps/backend/choreograph/runner.py'))
    monkeypatch.setattr(runner.signal, 'signal', lambda *_: None)
    ticks = []
    monkeypatch.setattr(runner, 'tick', lambda *args: ticks.append(args) or 0)
    monkeypatch.setattr(sys, 'argv', ['runner', '--once'])
    runner.main()
    assert len(ticks) == 1 and engine.queries == ['SELECT 1']
    assert runtime.closes == 1 and engine.disposed
    assert not (tmp_path / '.runtime/runner-ready.json').exists()
