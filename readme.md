### Setup

```
$ pip install -r requirements.txt
$ echo "key = 'MyTBAkey'" > keys.py
$ python main.py module fn args
```

### Protos

```
$ python -m grpc_tools.protoc --python_betterproto_out=protos/ -I=protos/ protos/*.proto
```

### Event Sims

```
# Schedule from real event
$ python main.py event_gen save_real_schedule <event_key>
# Schedule from fake event
$ python main.py event_gen generate in.txt
# Sim event
$ python main.py sim sim out/schedule.pb <year>
```
