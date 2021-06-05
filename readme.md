### Setup

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
# District from states in year
$ python main.py event_gen district_from_states "New York,NY" 2018
# Schedule from fake event
$ python main.py event_gen generate out/districts/New\ York-Ny_2018.txt 2018nycmp
# Sim event
$ python main.py sim sim out/fake_events/2018nycmp_schedule.pb 2018
# Save fake draft
$ python main.py sim save_draft out/fake_events/2018nycmp_faked.pb
```

### Formatting

```bash
$ isort --skip venv/ .; black --exclude venv .
```
