from py.cli import expose, pprint
from typing import Callable, List, Union, Dict
import yaml
import inflection


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

    def ref_to_proto(self, field_name: str, ref: str, n: int) -> str:
        field_type = ref.split("/")[-1]
        return field_type + " " + field_name + f" = {n};"

    def field_to_proto(
        self, field_name: str, data: dict, n: int
    ) -> Union[int, str, bool, float, list]:
        return self.get_fn_for_type(data["type"])(field_name, data, n)

    def int_field_to_proto(self, field_name: str, data: dict, n: int) -> str:
        return "int32 " + field_name + f" = {n};"

    def str_field_to_proto(self, field_name: str, data: dict, n: int) -> str:
        return "string " + field_name + f" = {n};"

    def bool_field_to_proto(self, field_name: str, data: dict, n: int) -> str:
        return "bool " + field_name + f" = {n};"

    def float_field_to_proto(self, field_name: str, data: dict, n: int) -> str:
        return "double " + field_name + f" = {n};"

    def array_field_to_proto(self, field_name: str, data: dict, n: int) -> str:
        if "$ref" in data["items"]:
            return "repeated " + self.ref_to_proto(
                field_name=field_name, ref=data["items"]["$ref"], n=n
            )

        inner_type = data["items"]["type"]

        s = self.get_fn_for_type(inner_type)(field_name, data["items"], n)
        if inner_type == "object":
            split = s.split("\n")
            split[-1] = "repeated " + split[-1]
            s = "\n".join(split)
        else:
            s = "repeated " + s

        return s

    def object_field_to_proto(self, field_name: str, data: dict, n: int) -> str:
        if "properties" in data and len(data["properties"].keys()) > 0:
            model = Model(inflection.camelize(field_name), data).to_proto()
            return (
                f"{model}\n{inflection.camelize(field_name)} {field_name} = " + f"{n};"
            )

        return "map<string, string> " + field_name + f" = {n};"

    def to_proto(self):
        fields = []

        if "properties" not in self.data:
            return ""

        for index, (field_name, field_data) in enumerate(
            self.data["properties"].items(), start=1
        ):
            if "$ref" in field_data:
                fields.append(
                    self.ref_to_proto(
                        field_name=field_name, ref=field_data["$ref"], n=index
                    )
                )
            else:
                fields.append(
                    self.field_to_proto(field_name=field_name, data=field_data, n=index)
                )

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

    models = [Model(k, v) for k, v in components["schemas"].items()]
    for m in models:
        print(m.to_proto())
