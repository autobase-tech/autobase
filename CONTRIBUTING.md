# Contributing Guide

This repository contains the MIT-licensed [automation core](./automation/) and [Autobase Platform deployment files](./console/).

You can help improve this project by:

- [Creating an issue](https://docs.github.com/issues/tracking-your-work-with-issues/creating-an-issue) after checking [open issues](https://github.com/autobase-tech/autobase/issues)
- [Submitting a pull request](https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) to fix a problem or add a feature

Your contributions are appreciated and will be taken seriously.

## How to Contribute

### 1. Create an issue

Report problems or suggest improvements by [creating an issue](https://github.com/autobase-tech/autobase/issues).

### 2. Fork the project

[Fork the repository](https://github.com/autobase-tech/autobase) into your GitHub account.

### 3. Make changes

Clone your fork locally and make the necessary changes:

```bash
git clone git@github.com:YOURNAMESPACE/autobase.git
cd autobase
```

### 4. Test your changes

Install [make](https://www.gnu.org/software/make/), [Python](https://www.python.org/), [venv](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/), and [Docker](https://docs.docker.com/engine/install/).

Run `make` to see the available commands.

> **Resource requirements**:
>
> - `make molecule-converge` — creates 3 containers and deploys a PostgreSQL cluster. **Minimum: 4 GB RAM, 2 CPU cores, 10 GB disk** (8 GB RAM recommended).
> - `make tests` — runs all test scenarios and is significantly more resource-intensive. **Minimum: 8 GB RAM, 4 CPU cores, 20 GB disk** (16 GB RAM recommended).
>
> On systems with limited RAM, use `make molecule-converge` for a quick functional test, then `make molecule-destroy` to clean up.

1. Create a virtual environment and install dependencies: `make bootstrap-dev`
2. Format your changes: `make prettier`
3. Lint your changes: `make lint`
4. Run the tests: `make molecule-converge` (lightweight) or `make tests` (all scenarios)

To test a specific distribution, set `IMAGE_NAMESPACE` and `IMAGE_DISTRO`:

```bash
IMAGE_NAMESPACE=geerlingguy IMAGE_DISTRO=debian13 make molecule-converge
```

### 5. Submit a pull request

[Create a pull request](https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork) and [refer to the issue number](https://docs.github.com/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls) using #123, where 123 is the issue number.

### 6. Wait

Your pull request will be reviewed, and you’ll receive feedback. Thanks for contributing!
