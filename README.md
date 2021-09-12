# `timeflip-tt`

A lightweight custom time tracker based on TimeFlip.

## Install and use

Install:

```bash
pip install --upgrade git+https://github.com/pierre-24/timeflip-tt.git
```

**NOTE:** async class-based views will only be supported in Flask 2.0.2, since [it was corrected latter](https://github.com/pallets/flask/pull/4113).
I [currently rely](requirements.in) on the development version of Flask that implemented the fix.

```bash
timeflip-tt -I  # create the config + database
timeflip-tt -i config.yml  # launch the application + webserver
```