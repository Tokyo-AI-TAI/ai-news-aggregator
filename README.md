# AI News Aggregator

Scrape, extract, translate, summarize and send news right to your inbox.
The initial goal is to help you stay updated with the latest AI news in Japan,
including those that are only in Japanese.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

## About this project

This project started as an experiment by [@mariomeissner](https://github.com/mariomeissner). It is built almost in its entirety by Cursor, the AI powered code editor. Almost no code was edited manually in the process.

Feel free to self-host this project if you want to use it yourself, a hosted version is not available at this moment.

## Settings

Moved to [settings](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html).

## Setup

This project was created with cookiecutter-django. Visit the [cookiecutter-django documentation](https://cookiecutter-django.readthedocs.io/en/latest/index.html) for more information.

### Python with uv

Install `uv` by following the instructions [here](https://docs.astral.sh/uv/getting-started/installation/).

We are currently using Python version 3.12. Install it via your favorite approach, e.g. homebrew, pyenv, or uv. Make sure uv recognizes and picks up that version. See more details [here](https://docs.astral.sh/uv/guides/install-python/).

Then, you can set up your virtual environment by running:

```bash
uv sync --all-extras
```

This will create a virtual environment in `.venv` and install all the dependencies.

Activate the virtual environment by running:

```bash
source .venv/bin/activate
```

Or run your python commands with `uv run`:

```bash
uv run python manage.py <command>
```

### Pre-commit hooks

Install the pre-commit hooks by running (with activated environment, or with `uv run`):

```bash
pre-commit install
```

Make sure they run and pass by running:

```bash
pre-commit run --all
```

### Postgres

On macOS, you can install Postgres using Homebrew. We are using version 16:

```bash
brew install postgresql@16
```

Then, start the server:

```bash
brew services start postgresql@16
```

You might need to add the following to your `.zshrc` or `.bashrc`:

```bash
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
```

Generate a secure password for the `postgres` user:

```bash
openssl rand -hex 16
```

Create a superuser called `postgres`:

```bash
createuser -P -s postgres
```

Confirm that you can connect to the database:

```bash
psql postgres
```

(Ctrl-D to exit)

Create the database:

```bash
createdb --username=postgres news_aggregator
```

Create a `.env` file:

```bash
cp .envs.example .env
```

Replace the password with the one you generated earlier.

Finally, run the initial migrations:

```bash
uv run python manage.py migrate
```

Verify that you can run the development server:

```bash
uv run python manage.py runserver
```

And access the site via <http://localhost:8000/>.

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy news_aggregator

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html#using-webpack-or-gulp).

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd news_aggregator
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd news_aggregator
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd news_aggregator
celery -A config.celery_app worker -B -l info
```

### Email Server

In development, it is often nice to be able to see emails that are being sent from your application. If you choose to use [Mailpit](https://github.com/axllent/mailpit) when generating the project a local SMTP server with a web interface will be available.

1.  [Download the latest Mailpit release](https://github.com/axllent/mailpit/releases) for your OS.

2.  Copy the binary file to the project root.

3.  Make it executable:

        $ chmod +x mailpit

4.  Spin up another terminal window and start it there:

        ./mailpit

5.  Check out <http://127.0.0.1:8025/> to see how it goes.

Now you have your own mail server running locally, ready to receive whatever you send it.

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.

### Heroku

See detailed [cookiecutter-django Heroku documentation](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-on-heroku.html).
