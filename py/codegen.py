import inspect
import json
from collections import namedtuple
from typing import Callable, Dict, Union

import inflection
import yaml
from rich.pretty import pprint
from tqdm.std import tqdm

from py.cli import expose
from py.tpa.context_manager import tpa_cm
from py.util import CURRENT_YEAR, CURRENT_YEAR_RANGE, STATE_TO_SHORT


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
    content = None
    with open(filepath, "r") as f:
        content = f.readlines()

    content = yaml.load("".join(content), Loader=yaml.FullLoader)

    generate_models(content)
    generate_request_models(content)
    generate_rpcs(content)


def generate_models(content):
    schemas = content["components"]["schemas"]

    print('syntax = "proto3";')

    models = [Model(k, v) for k, v in schemas.items()]
    for m in models:
        print(m.to_proto())


def generate_request_models(content):
    parameters = content["components"]["parameters"]
    print("message Parameter {")

    for i, (param_name, param_data) in enumerate(parameters.items(), start=1):
        type_ = {"string": "string", "integer": "int32"}[param_data["schema"]["type"]]
        print(f" {type_} {inflection.underscore(param_name)} = {i};")

    print("}")

    print("message Response {")
    print("  oneof response_value {")
    print("    int32 int_value = 1;")
    print("    string string_value = 2;")
    print("    bool bool_value = 3;")
    print("    double double_value = 4;")
    print("  }")
    print("}")


def generate_rpcs(content):
    rpcs = "service TPA {\n"
    paths = content["paths"]

    Msg = namedtuple("Msg", ["message_name", "type_", "field_name"])
    msgs = set()
    param_name_to_type = {}
    # Pre-determine param types
    for param_name, param_data in content["components"]["parameters"].items():
        param_name_to_type[param_name] = {"string": "string", "integer": "int32"}[
            param_data["schema"]["type"]
        ]

    for path, path_data in paths.items():
        name = path_data["get"]["operationId"]
        comment = path_data["get"]["description"]

        return_schema = path_data["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]

        response_type = ""
        if "type" in return_schema:
            type_ = return_schema["type"]

            if type_ == "array":
                response_type = "stream "
                if "$ref" in return_schema["items"]:
                    type_ = return_schema["items"]["$ref"].split("/")[-1]
                else:
                    type_ = "Response"
        else:
            type_ = return_schema["$ref"].split("/")[-1]

        response_type += type_

        # Create Message type for the required args
        local_msgs = []
        for param_dict in path_data["get"]["parameters"]:
            if "$ref" not in param_dict:
                print(path, param_dict)
                raise Exception("$ref not in path params")

            ref_name = param_dict["$ref"].split("/")[-1]
            if ref_name == "If-Modified-Since":
                continue

            local_msgs.append(
                Msg(
                    message_name=inflection.camelize(inflection.underscore(ref_name)),
                    type_=param_name_to_type[ref_name],
                    field_name=inflection.underscore(ref_name),
                )
            )
        if len(local_msgs) == 0:
            continue

        param_name = "".join([m.message_name for m in local_msgs])
        msg_str = f"message {param_name} {{\n"
        for i, msg in enumerate(local_msgs, start=1):
            msg_str += f"  {msg.type_} {msg.field_name} = {i};\n"
        msg_str += "}\n"
        msgs.add(msg_str)

        rpcs += f"  /* {comment} */\n"
        rpcs += f"  rpc {name}({param_name}) returns ({response_type}) {{}}\n"

    rpcs += "}\n"
    for msg in msgs:
        print(msg)
    print(rpcs)


@expose
def generate_server():
    # only need to ever run once. generates py.tpa.tpa_server starting points.
    print("from protos import *")
    print("class TPAService(TpaBase):")

    from protos import TpaBase

    for method_name in dir(TpaBase):
        if method_name.startswith("get_"):
            print(
                f"    async def {method_name}{inspect.signature(getattr(TpaBase, method_name))}:"
            )
            print(f"        print('called {method_name}')")
            print("        return None")


@expose
async def regions():
    hand_map_states = {
        "USA": {
            "California": ["CA"],
            "Midwest": [
                "OK",
                "ND",
                "SD",
                "KS",
                "WI",
                "IL",
                "NE",
                "MO",
                "IA",
            ],
            "Desert": ["NV", "AZ"],
            "New York": ["NY"],
            "Bluegrass": ["TN", "KY"],
            "Mountain": ["CO", "UT", "ID", "WY", "MT"],
            "South": ["AR", "LA", "MS", "AL"],
            "Florida": ["FL"],
            "Minnesota": ["MN"],
            "WOW": ["WV", "OH", "PA"],
            "South Carolina": ["SC"],
            "Hawaii": ["HI"],
        },
        "Canada": {
            "Quebec": ["QC", "NS", "NB"],
            "Alberta": ["AB", "SK"],
            "British Columbia": ["BC"],
        },
    }

    hand_map_countries = {
        **{
            "Europe": [
                "United Kingdom",
                "Kingdom",
                "Armenia",
                "Italy",
                "Bosnia-Herzegovina",
                "Spain",
                "Denmark",
                "Greece",
                "France",
                "Netherlands",
                "Switzerland",
                "Croatia",
                "Czech Republic",
                "Germany",
                "Poland",
                "Sweden",
                "Norway",
            ],
            "South America": ["Brazil", "Chile", "Colombia", "Paraguay", "Ecuador"],
            "China": ["China", "Chinese Taipei"],
            "Africa": ["Ethiopia", "South Africa", "Libya"],
            "Oceania": ["Vietnam", "New Zealand", "Japan", "Indonesia", "Singapore"],
        },
        **{c: [c] for c in ["Australia", "Turkey", "Mexico", "Israel"]},
    }

    async with tpa_cm() as tpa:
        region = {}
        for year in tqdm(range(1992, CURRENT_YEAR_RANGE)):
            async for district in tpa.get_districts_by_year(year=year):
                async for district_team in tpa.get_district_teams(
                    district_key=district.key
                ):
                    region[district_team.key] = district.abbreviation

            async for team in tpa.get_all_teams_by_year(year=year):
                if team.key not in region:
                    if team.country in ["USA", "Canada"]:
                        for region_name, region_states in hand_map_states[
                            team.country
                        ].items():
                            if STATE_TO_SHORT[team.state_prov] in region_states:
                                region[team.key] = region_name
                    else:
                        for region_name, region_countries in hand_map_countries.items():
                            if team.country in region_countries:
                                region[team.key] = region_name

        with open("py/data/all_regions.json", "w+") as f:
            print(json.dumps(region), file=f)
