import math
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Union

import matplotlib.pyplot as plt
import networkx as nx
from tqdm import tqdm

from py.cli import expose
from py.data.graphs import *
from py.tba import tba
from py.util import create_dir_if_not_exists, team_key_to_num


class GraphSaver:
    def __init__(
        self,
        graph: Union[nx.Graph, nx.DiGraph],
        name: str,
        base: str = "out",
        progs=["dot", "neato", "fdp", "sfdp"],
        layouts=[
            nx.spring_layout,
            nx.planar_layout,
            nx.kamada_kawai_layout,
            nx.spiral_layout,
            nx.shell_layout,
            nx.circular_layout,
        ],
        node_size=1000,
        font_size=10,
        rough_figure_size=5000,
        flat=False,
    ) -> None:
        self.graph = graph
        self.name = name
        self.base = base
        self.progs = progs
        self.layouts = layouts
        self.node_size = node_size
        self.font_size = font_size
        self.rough_figure_size = rough_figure_size
        self.flat = flat
        fig = plt.figure(figsize=(rough_figure_size / 100, rough_figure_size / 100))
        fig.show()

    def save(self):
        self.save_graphviz()
        self.save_dotfiles()
        self.save_nxlayouts()

    def __save_posit(self, posit: dict, path: str):
        nx.draw_networkx(
            self.graph,
            posit,
            with_labels=True,
            node_color="white",
            edgecolors="black",
            node_size=self.node_size,
            font_size=self.font_size,
        )

        edge_labels = {
            k: v
            for k, v in nx.get_edge_attributes(self.graph, "weight").items()
            if v > 1
        }

        nx.draw_networkx_edge_labels(self.graph, posit, edge_labels=edge_labels)
        plt.savefig(path, bbox_inches="tight")
        plt.clf()

    def get_ag_path(self):
        if self.flat:
            return f"{self.base}/{self.name}/"
        else:
            return f"{self.base}/{self.name}/agraph/"

    def get_gv_path(self):
        if self.flat:
            return f"{self.base}/{self.name}/"
        else:
            return f"{self.base}/{self.name}/graphviz/"

    def get_dotfile_path(self):
        if self.flat:
            return f"{self.base}/{self.name}/"
        else:
            return f"{self.base}/{self.name}/dotfiles/"

    def get_nx_path(self):
        if self.flat:
            return f"{self.base}/{self.name}/"
        else:
            return f"{self.base}/{self.name}/nxlayouts/"

    def save_graphviz(self):
        create_dir_if_not_exists(self.get_gv_path())
        create_dir_if_not_exists(self.get_ag_path())

        edge_labels = {
            k: v
            for k, v in nx.get_edge_attributes(self.graph, "weight").items()
            if v > 1
        }
        agraph = nx.nx_agraph.to_agraph(self.graph)
        for edge in agraph.edges():
            edge_fixed = (str(edge[0]), str(edge[1]))
            if edge_fixed in edge_labels:
                edge.attr["label"] = edge_labels[edge_fixed]

        for prog in tqdm(self.progs):
            posit = nx.nx_pydot.pydot_layout(self.graph, prog=prog)
            self.__save_posit(posit, f"{self.get_gv_path()}gv_{prog}.png")
            agraph.draw(f"{self.get_ag_path()}ag_{prog}.png", prog=prog)

    def save_dotfiles(self):
        create_dir_if_not_exists(self.get_dotfile_path())
        with open(f"{self.get_dotfile_path()}out.dot", "w+") as f:
            nx.nx_pydot.write_dot(self.graph, f)

    def save_nxlayouts(self):
        create_dir_if_not_exists(self.get_nx_path())
        for layout_fn in tqdm(self.layouts):
            kwargs = {}
            if layout_fn == nx.spring_layout:
                kwargs["k"] = 10 * 1 / math.sqrt(self.graph.order())

            try:
                pos = layout_fn(self.graph, **kwargs)
                self.__save_posit(
                    pos,
                    f"{self.get_nx_path()}nx_{layout_fn.__name__}.png",
                )
            except nx.NetworkXException:
                pass


History = Dict[str, List[List[int]]]


class MentorGraphSaver(GraphSaver):
    def __init__(
        self,
        mentor_history: History,
        name: str,
        base: str = "out",
        progs=["dot", "neato", "fdp", "sfdp"],
        layouts=[
            nx.spring_layout,
            nx.planar_layout,
            nx.kamada_kawai_layout,
            nx.spiral_layout,
            nx.shell_layout,
            nx.circular_layout,
        ],
        node_size=1000,
        font_size=10,
        rough_figure_size=5000,
        flat=False,
    ) -> None:
        g = nx.DiGraph()
        g.add_nodes_from(self.get_nodes(mentor_history))
        self.add_edges(g, mentor_history)

        super().__init__(
            g,
            name,
            base=base,
            progs=progs,
            layouts=layouts,
            node_size=node_size,
            font_size=font_size,
            rough_figure_size=rough_figure_size,
            flat=flat,
        )

    @classmethod
    def get_nodes(cls, history: History) -> Set[int]:
        l = set()
        for _, team_history in history.items():
            for moment in team_history:
                for team in moment:
                    l.add(str(team))

        return l

    @classmethod
    def get_edges(cls, history: History) -> List[Tuple[str, int, int]]:
        edges = []
        for person, team_history in history.items():
            num_moments = len(team_history)
            for i in range(num_moments - 1):
                moment_a = team_history[i]
                moment_b = team_history[i + 1]
                for team_a in moment_a:
                    for team_b in moment_b:
                        if team_a == team_b:
                            continue

                        edges.append((person, str(team_a), str(team_b)))

        return edges

    @classmethod
    def get_weights(cls, history: History) -> Dict[Tuple[int, int], int]:
        weights = defaultdict(lambda: 0)
        seen = defaultdict(set)
        edges = cls.get_edges(history)
        for person, a, b in edges:
            if person in seen[(a, b)]:
                continue

            seen[(a, b)].add(person)
            weights[(a, b)] += 1

        return weights

    @classmethod
    def add_edges(cls, graph: nx.DiGraph, history: History):
        edges = cls.get_edges(history)
        weights = cls.get_weights(history)

        for _, team_a, team_b in edges:
            graph.add_edge(team_a, team_b, weight=weights[(team_a, team_b)])


@expose
def save(name):
    MentorGraphSaver(
        mentor_history=globals()[name],
        name=name,
    ).save()


@expose
def einstein():
    edges = set()

    def get_alliance_edges(teams):
        l = []
        for t1 in teams:
            for t2 in teams:
                if t1 == t2:
                    continue

                l.append((team_key_to_num(t1), team_key_to_num(t2)))

        return l

    keys = [f"{y}cmp" for y in range(2002, 2017)]
    keys.extend(["2017cmpmo", "2017cmptx"])
    keys.extend(["2018cmpmi", "2018cmptx"])
    keys.extend(["2019cmpmi", "2019cmptx"])

    for k in tqdm(keys):
        try:
            alliances = tba.event_alliances(event=k)
            for alliance in alliances:
                edges.update(get_alliance_edges(alliance["picks"]))
        except:
            matches = tba.event_matches(event=k)
            for match in matches:
                for c in ["red", "blue"]:
                    edges.update(get_alliance_edges(match["alliances"][c]["team_keys"]))

    g = nx.Graph()
    g.add_edges_from(edges)

    GraphSaver(g, f"einstein", rough_figure_size=5000).save()
