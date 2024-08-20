# Pare

Pare is the easiest way to deploy Python Lambdas alongside your primary web application.

[Discord](https://discord.gg/Kz2TnszerR)


## Why use Pare?

Pare is built to allow web developers to independently scale parts of a web application.
More specifically, Pare is useful if you have functions which are:

- compute intensive
- blocking
- relatively isolated
- parallel

Some examples are **document parsing**, **data aggregation**, **webhook handling** and **image processing**.

## Quickstart

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
> pare delete quickstart --git-hash 8a4096b
```


## Advanced