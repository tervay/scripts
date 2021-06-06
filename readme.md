### Setup

```bash
$ pip install -r requirements.txt
$ echo "key = 'MyTBAkey'" > key.py
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
$ python main.py event_gen create in.txt
$ python main.py sim sim out/fake_events/2019nycmp/2019nycmp_fe.pb
$ python main.py sim save_draft out/fake_events/2019nycmp/2019nycmp_fe.pb
$ python main.py event_gen tba out/fake_events/2019nycmp/2019nycmp_fe.pb
```

### Formatting

```bash
$ isort --skip venv/ .; black --exclude venv .
```
