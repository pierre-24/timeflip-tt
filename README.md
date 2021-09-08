# `timeflip-tt`

A lightweight custom time tracker based on TimeFlip.

## Install and use

Install:

```
pip install (...)
```

**NOTE:** async class-based views will only be supported in Flask 2.0.2, since [it was corrected latter](https://github.com/pallets/flask/pull/4113).
I [currently rely](requirements.in) on the development version of Flask that implemented the fix.

Usage:

```
timeflip-tt -a xxx -p xxx (...)
```