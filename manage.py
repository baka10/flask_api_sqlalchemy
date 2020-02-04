from flask_script import Manager, Server
from flask_migrate import MigrateCommand

from semantive.factory import create_app

import os

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, "tests")

app = create_app()
manager = Manager(app)


def _make_context():
    """
    Return context dict for a shell session so you can access app, db, and the models by default
    """
    return {"app": app}


@manager.command
def test():
    """
    Run the tests
    """
    import pytest
    exit_code = pytest.main([TEST_PATH, "--versobe"])
    return exit_code


manager.add_command("server", Server())
manager.add_command("db", MigrateCommand)

if __name__ == "__main__":
    manager.run()
