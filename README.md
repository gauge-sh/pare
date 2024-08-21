# 🔪 Pare

[![version](https://img.shields.io/pypi/v/pare.svg)](https://pypi.Python.org/pypi/pare)
[![license](https://img.shields.io/pypi/l/pare.svg)](https://pypi.Python.org/pypi/pare)
[![python](https://img.shields.io/pypi/pyversions/pare.svg)](https://pypi.Python.org/pypi/pare)
[![ci](https://github.com/gauge-sh/pare/actions/workflows/ci.yml/badge.svg)](https://github.com/gauge-sh/pare/actions/workflows/ci.yml)
[![pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Pare is the easiest way to deploy Python Lambdas alongside your primary web application.

[Discord](https://discord.gg/Kz2TnszerR)

![pare_demo](https://github.com/user-attachments/assets/2513eb92-51f3-45c6-9eb3-0b71dafe8a48)


## Why use Pare?

Pare is built to allow web developers to independently scale parts of a web application.
More specifically, Pare is useful if you have functions which are:

- compute intensive
- blocking
- isolated
- parallel

Some examples are **document parsing**, **data aggregation**, **webhook handling** and **image processing**.

With Pare, you can offload these tasks from your main web server, while also getting automatic scaling for concurrent requests.

## Quickstart

```shell
> pip install pare
```

First, mark the function you want to deploy onto a Lambda:

```python
import pare

@pare.endpoint(name="quickstart")
def my_function(*args, **kwargs):
    ...
```

This will tell Pare to use this function as the Lambda handler.

Calling the function in your code will still execute locally, but the decorator adds additional methods to make calls to the deployed Lambda.

```python
from my_module import my_function

my_function(*args, **kwargs)  # local function call

my_function.invoke(*args, **kwargs)  # remote Lambda call

await my_function.invoke_async(*args, **kwargs)  # async remote Lambda call
```


Next, login with Github to get a Pare API Key:

```shell
> pare login
Please visit: https://github.com/login/device
and enter code: 1111-1111
```

Following the on-screen instructions will authorize Gauge to retrieve your Github username and email for the purposes of account creation. The token has no other permissions.

After logging in, you can run a deploy of your function into the Pare Cloud:

```shell
> pare deploy my_module.py
```

> [!NOTE]
> This generally takes between 3s (when heavily cached) and 60s (no cache, heavy dependencies)

Once the deploy is finished, you can verify with `pare status`:

```shell
> pare status
                      Deployment Data                      
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                   ┃ Git Hash ┃ Created At          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ quickstart             │ 8a4096b  │ 2024-08-19 22:55:51 │
└────────────────────────┴──────────┴─────────────────────┘
```

That's it! Your function is now serverless.


To delete a deployed function, use `pare delete`:

```shell
> pare delete quickstart
```


## Notes on Deployment

The `pare deploy` command accepts a sequence of file patterns (filepaths, directories, or glob paths).
The corresponding files will be collected into a single bundle, which will be built and deployed with each function.

The entrypoint for each function will be defined by `pare.endpoint`, and it is critical that
all of the entrypoint's imports are included in the bundle.

Third party dependencies are bundled
with each function individually, see the section below for more details.

In the future, we plan to use the technology behind [Tach] to automatically determine
the transitive dependencies in your project and create a complete bundle. Reach out on [Discord](https://discord.gg/Kz2TnszerR)
if this is an important feature for you!


## Advanced Usage


### 3rd Party Dependencies

Pare allows installing 3rd party dependencies from PyPI for each deployed function.

Use the `dependencies` kwarg in the `endpoint` decorator to specify the dependencies for a function,
and they will automatically be installed during the deploy.

```python
@pare.endpoint(name="3rd-party-deps", dependencies=["pydantic", ...])
```

The dependency names can specify version numbers as well, just as if they were listed in `requirements.txt`.

```python
@pare.endpoint(name="3rd-party-deps", dependencies=["pydantic==2.8.2", ...])
```

> [!TIP]
> If you want to quickly determine the 3rd party dependencies used by a set of files, consider using [Tach](https://github.com/gauge-sh/tach) with [`tach report-external`](https://docs.gauge.sh/usage/commands#tach-report-external)

### Environment Variables

Pare allows setting environment variables for your functions during the deploy.

Use the `-e` option to set environment variables:

```shell
> pare deploy my_module.py -e MY_VARIABLE=myvalue -e OTHER_VARIABLE=othervalue [...]
```


### Atomic Deployment

Pare supports 'atomic deployment' of services based on a git hash.

When atomic deployment is disabled (the default),
the Pare API will route requests by name to the latest deployed version of your function.

When atomic deployment is enabled, the Pare SDK will include the git hash in its requests to your deployed functions,
and the Pare API will route your request to the service with a matching git hash.

This feature is enabled on the client-side with the environment variable `PARE_ATOMIC_DEPLOYMENT_ENABLED`.

Since your main application likely will not have access to `git` to determine its git hash at runtime,
you will need to set the `PARE_GIT_HASH` environment variable during your build and deployment pipeline.
