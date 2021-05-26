from py.cli import expose, pprint
from typing import Callable, List, Union, Dict
import yaml


class Model:
    def __init__(self, name: str, data: Dict[str, dict]) -> None:
        self.data = data
        self.name = name
        self.fns = {
            "integer": self.int_field_to_proto,
            "string": self.str_field_to_proto,
            "boolean": self.bool_field_to_proto,
            "number": self.float_field_to_proto,
            "array": self.array_field_to_proto,
            "object": self.object_field_to_proto,
        }

    def get_fn_for_type(self, field_type: str) -> Callable:
        if field_type not in self.fns:
            raise Exception(
                f"Cannot generate protofield for unmapped type {field_type}"
            )

        return self.fns[field_type]

    def ref_to_proto(self, field_name: str, ref: str) -> str:
        field_type = ref.split("/")[-1]
        return field_type + " " + field_name + " = {n};"

    def field_to_proto(
        self, field_name: str, data: dict
    ) -> Union[int, str, bool, float, list]:
        return self.get_fn_for_type(data["type"])(field_name, data)

    def int_field_to_proto(self, field_name: str, data: dict) -> str:
        return "int32 " + field_name + " = {n};"

    def str_field_to_proto(self, field_name: str, data: dict) -> str:
        return "string " + field_name + " = {n};"

    def bool_field_to_proto(self, field_name: str, data: dict) -> str:
        return "bool " + field_name + " = {n};"

    def float_field_to_proto(self, field_name: str, data: dict) -> str:
        return "double " + field_name + " = {n};"

    def array_field_to_proto(self, field_name: str, data: dict) -> str:
        if "$ref" in data["items"]:
            return "repeated " + self.ref_to_proto(
                field_name=field_name, ref=data["items"]["$ref"]
            )

        inner_type = data["items"]["type"]
        return "repeated " + self.get_fn_for_type(inner_type)(field_name, data)

    def object_field_to_proto(self, field_name: str, data: dict) -> str:
        return "MapObject " + field_name + " = {n};"

    def to_proto(self):
        fields = []

        if "properties" not in self.data:
            return ""

        for field_name, field_data in self.data["properties"].items():
            if "$ref" in field_data:
                fields.append(
                    self.ref_to_proto(field_name=field_name, ref=field_data["$ref"])
                )
            else:
                fields.append(
                    self.field_to_proto(field_name=field_name, data=field_data)
                )

        fields = [f.format(n=i) for i, f in enumerate(fields, start=1)]
        header = f"message {self.name} {{"
        footer = "}"

        return header + "\n" + "\n".join(fields) + "\n" + footer


@expose
def generate_pbs(filepath):
    generate_models(filepath)


def generate_models(filepath):
    content = None
    with open(filepath, "r") as f:
        content = f.readlines()

    content = yaml.load("".join(content), Loader=yaml.FullLoader)
    components = content["components"]

    print('syntax = "proto3";')
    print("message MapObject {")
    print("  map<string, string> data = 1;")
    print("}")

    models = [Model(k, v) for k, v in components["schemas"].items()]
    for m in models:
        print(m.to_proto())
