PIP := "./venv/bin/python -m pip --require-venv"

# Display recipe listing
help:
    @just --list

# Update all dev dependencies
update:
    echo Installing when ...
    {{PIP}} install -U -e .

    echo Installing dev dependencies ...
    {{PIP}} install -U pytest coverage pytest-cov tox ipython flake8 black twine bump isort

# Create a virtual environment if needed
venv: && update
    #!/usr/bin/env bash
    if [ ! -d ./venv ]; then
        echo Creating virtual env in dir ./venv ...
        python3 -m venv venv
    fi 

# Run test suite
test:
    ./venv/bin/pytest -vv -s

# Remove the virtual env dir
rmvenv:
    #!/usr/bin/env bash
    if [ -d ./venv ]; then
        if [ -s $VIRTUAL_ENV ]; then
            echo You must now run `deactivate` manually
        fi
        rm -rf ./venv
    fi

# Run coverage report from test suite
cov:
    ./venv/bin/pytest -vv -s --cov-config setup.cfg --cov-report html --cov-report term --cov=when
    echo HTML coverage report: ./build/coverage/index.html
    open ./build/coverage/index.html

# Remove all *.pyc files and __pycache__ dirs
clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete

# Remove all test and coverage artifacts
clean-test:
    rm -rf .coverage
    rm -rf ./pytest_cache ./.tox

# Remove all build and dist artifacts
clean-build:
    rm -rf ./src/when.egg-info ./dist ./build

# Clean all build, test, and compile artifacts and remove venv
[confirm('Remove all build, test, coverage, and compiled artifacts and delete venv?')]
purge: clean clean-test rmvenv clean-build
    echo All artifacts purged

# Run linter and code formatter tools
lint:
    ./venv/bin/flake8 src/when tests
    ./venv/bin/black --check --diff -l 100 src/when tests setup.py

# Show current version
version:
    #!/usr/bin/env python3
    local_ctx = {}
    with open("src/when/__init__.py") as fp:
        exec(fp.read(), {}, local_ctx)
    print(f"Current version: {local_ctx['VERSION']}")

# Launch sqlite data browser (macOS only)
[macos]
db:
    open ./src/when/db/when.db

