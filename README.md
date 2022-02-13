# Integrity Research - Web Scraping API

## Run API tests

* Start in VSCode the Azure Functions app by pressing F5
* Import in [Postman](https://www.postman.com/downloads/) the collection and environment included in the root of this project
* Set the environment to be used with the collection
* Run API requests from the collection

## Configure code formatter and linter

This project uses [Black](https://github.com/pycqa/flake8) for formatting and [Flake8](https://github.com/pycqa/flake8) for linting the code.

### File save

The code formatter and linter are configured to automatically run on file save.

### Pre-commit hooks

The code formatter and linter can be enabled to automatically run for each of the files included in the  commit.

To enable pre-commit hooks perform the following actions:

* Install [pre-commit](https://pre-commit.com)

```bash
pip install pre-commit
```

* (done) The git hooks were already defined in the root of the project in file

```text
.pre-commit-config.yaml
```

* Update hook repositories to latest versions

```bash
pre-commit autoupdate
```

* Install the git hook scripts in the ```.git/``` folder

```bash
pre-commit install
```

* (optional) Run for all files

```bash
pre-commit run --all-files
```
