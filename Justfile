set export
set positional-arguments

DEV := "./.dev"
VENV := DEV / "venv"
BIN := VENV / "bin"
PIP := BIN / "python -m pip --require-venv"


# Display recipe listing
help:
    @just --list

info:
    @echo dev = {{DEV}}
    @echo venv = {{VENV}}
    @echo bin = {{BIN}}
    @echo pip = {{PIP}}

# Update all dev dependencies
update:
    @echo Installing when ...
    {{PIP}} install -U -e .

    @echo Installing dev dependencies ...
    {{PIP}} install -U \
        build \
        pytest \
        docutils \
        pytest-sugar \
        pytest-clarity \
        freezegun \
        responses \
        coverage \
        tox \
        ipython \
        flake8 \
        black \
        twine \
        bump \
        isort

# Create a virtual environment if needed
venv:
    #!/usr/bin/env bash
    if [ ! -d {{VENV}} ]; then
        echo Creating virtual env in dir {{VENV}} ...
        python3 -m venv {{VENV}}
    fi 

# Create virtual environment and install / update all dev dependencies
init: info venv update
    @echo Initialization complete

# Run test suite
test *args='':
    {{BIN}}/pytest -vv -s --diff-width=60 "$@"

# Run test suite
retest:
    {{BIN}}/pytest -vv -s --diff-width=60 --lf

# Run all tox tests
test-all:
    {{BIN}}/tox

# Run coverage report from test suite
cov:
    -{{BIN}}/coverage run -m pytest -vv -s
    -{{BIN}}/coverage report --fail-under=95 --omit "__main__.py"
    {{BIN}}/coverage html
    echo HTML coverage report: {{DEV}}/coverage/index.html
    # open {{DEV}}/coverage/index.html

# Remove the virtual env dir
rmvenv:
    #!/usr/bin/env bash
    if [ -d {{VENV}} ]; then
        if [ -s $VIRTUAL_ENV ]; then
            echo You must now run `deactivate` manually
        fi
        rm -rf {{VENV}}
    fi

# Remove all *.pyc files and __pycache__ dirs
clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete

clean-dev:
    rm -rf {{DEV}}

# Remove all build and dist artifacts
clean-build:
    rm -rf ./src/when.egg-info ./.dev/dist

# Clean all build, test, and compile artifacts and remove venv
[confirm('Remove all build, test, coverage, and compiled artifacts and delete venv?')]
purge: clean clean-dev rmvenv clean-build
    echo All artifacts purged

# Build sdist and wheel files for distribution
build:
    {{BIN}}/python -m build --outdir ./.dev/dist

# Run linter and code formatter tools
lint:
    @echo Linting...
    -{{BIN}}/flake8 src/when tests

    @echo Format checks...
    -{{BIN}}/black --check --diff -l 100 src/when tests

# Launch sqlite data browser (macOS only)
[macos]
db:
    open `when --prefix`/db/when.db

strftime:
    #!/usr/bin/env python3
    import prettytable
    from when.config import FORMAT_SPECIFIERS
    pt = prettytable.PrettyTable(
        field_names=["Spec", "Replacement", "Example", "Note"],
        max_width=72,
    )
    pt.align["Replacement"] = "l"
    pt.align["Example"] = "l"
    pt.hrules = True
    pt.add_rows(FORMAT_SPECIFIERS)
    print(
        f"Format Specifiers:\n{pt.get_string()}\n\n"
        "Notes:\n* - Locale-dependent\n+ - C99 extension\n! - when extension"
    )

# Execute the when command with any arbitrary arguments
when *args:
    @{{BIN}}/when "$@"

