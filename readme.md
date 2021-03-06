### Setup

```bash
$ sudo apt-get install python3-dev graphviz libgraphviz-dev pkg-config
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
$ python main.py event_gen district_from_states "NY,MA" 2018
$ python main.py event_gen fair_divisions out/districts/NY-MA-VT-CT-RI-NH-ME-PA-NJ-DE_2018_pts.txt 4
$ python main.py event_gen create in.txt
$ python main.py sim sim out/fake_events/2019nycmp/2019nycmp_fe.pb
$ python main.py sim save_draft out/fake_events/2019nycmp/2019nycmp_fe.pb
$ python main.py event_gen tba out/fake_events/2019nycmp/2019nycmp_fe.pb
```
or
```bash
$ python main.py event_gen district_from_all 2019
$ python main.py event_gen create_and_sim_district out/districts/all_2019_pts.txt 8
```


### Formatting

```bash
$ isort --skip venv/ .; black --exclude venv .
```
