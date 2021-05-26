### Setup

```
$ pip install -r requirements.txt
$ echo "key = 'MyTBAkey'" > keys.py
$ python main.py module fn args
```

### Protos

```
$ python -m grpc_tools.protoc --python_betterproto_out=protos/ --grpc_python_out=protos/ -I=protos/ protos/tba.proto 
```
