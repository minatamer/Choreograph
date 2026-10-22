from choreograph.settings import Settings


def test_settings_repr_keeps_only_nonsecret_diagnostics():
    values = ('postgresql+psycopg://synthetic-password-marker@localhost/test',
              'http://127.0.0.1:45860', 'synthetic-bridge-marker', 'synthetic-token-marker')
    settings = Settings(*values, testing=True)
    shown = repr(settings)
    assert all(value not in shown for value in (values[0], values[2], values[3]))
    assert settings.database_url == values[0] and settings.bridge_secret == values[2] and settings.token_key == values[3]
    assert values[1] in shown and "profile='fake'" in shown and 'testing=True' in shown
