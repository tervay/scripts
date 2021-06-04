### Setup

You'll need to set up GDAL. It's a pain. Sorry.

```bash
$ sudo add-apt-repository ppa:ubuntugis/ppa
$ sudo apt-get update
$ sudo apt-get install gdal-bin libgdal-dev
```

Edit `~/.bashrc` and append these lines:

```bash
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
```

```bash
$ pip install -r requirements.txt
$ echo "key = 'MyTBAkey'" > keys.py
$ python main.py tpa
$ python main.py module fn args
```

`python main.py tpa` will run the cache layer / protobuf proxy.

### Protos

```bash
$ python -m grpc_tools.protoc --python_betterproto_out=protos/ -I=protos/ protos/*.proto
```

### Event Sims

```bash
# Schedule from real event
$ python main.py event_gen save_real_schedule <event_key>
# Schedule from fake event
$ python main.py event_gen generate in.txt
# Sim event
$ python main.py sim sim out/schedule.pb <year>
```
