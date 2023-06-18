# What is this?

This is a part of a distributed systems project. To understand the project as a whole look at [this repo](https://github.com/Ziad-Nasr/Multiplayer-2DCarRacing).

# How to run this?

You will need to install ZMQ using pip

Then run

```bash
python Tracker.py
```

or to keep a server up after terminating an SSH session.

```bash
disown $(python Tracker.py) &
```

Please note: you need to change the value of IP to be your server's ip address.

