class Graph:
    """图数据结构，节点包含下标（唯一标识）和值，支持自动创建节点"""

    class Node:
        __slots__ = ('index', 'value')
        def __init__(self, index, value):
            self.index = index
            self.value = value

        def __repr__(self):
            return f"Node({self.index}, {self.value})"

    def __init__(self, node_count, directed=False):
        """
        参数:
            node_count: 初始节点数量，下标为 0 到 node_count-1
            directed:   是否为有向图，默认无向
        """
        self.directed = directed
        self.nodes = {}          # index -> Node
        self.adj = {}            # index -> set(邻接下标)

        for i in range(node_count):
            self.add_node(i, i)  # 默认值等于下标，可自行修改

    def add_node(self, index, value):
        """添加节点，下标必须唯一"""
        if index in self.nodes:
            raise ValueError(f"节点下标 {index} 已存在")
        node = self.Node(index, value)
        self.nodes[index] = node
        self.adj.setdefault(index, set())
        return node

    def add_edge(self, from_idx, to_idx):
        """添加边（两个节点必须已存在）"""
        if from_idx not in self.nodes:
            raise KeyError(f"节点 {from_idx} 不存在")
        if to_idx not in self.nodes:
            raise KeyError(f"节点 {to_idx} 不存在")
        self.adj[from_idx].add(to_idx)
        if not self.directed:
            self.adj[to_idx].add(from_idx)

    def remove_node(self, index):
        """删除节点及其所有关联边"""
        if index not in self.nodes:
            raise KeyError(f"节点 {index} 不存在")
        del self.nodes[index]
        # 删除其他节点中指向该节点的边
        for neighbour_set in self.adj.values():
            neighbour_set.discard(index)
        del self.adj[index]

    def remove_edge(self, from_idx, to_idx):
        """删除边"""
        if from_idx in self.adj and to_idx in self.adj[from_idx]:
            self.adj[from_idx].remove(to_idx)
        if not self.directed and to_idx in self.adj and from_idx in self.adj[to_idx]:
            self.adj[to_idx].remove(from_idx)

    def get_node(self, index):
        """获取节点对象"""
        return self.nodes.get(index)

    def neighbors(self, index):
        """返回指定节点的邻居节点列表（Node对象）"""
        if index not in self.adj:
            raise KeyError(f"节点 {index} 不存在")
        return [self.nodes[nei] for nei in self.adj[index]]

    def __contains__(self, index):
        return index in self.nodes

    def __len__(self):
        return len(self.nodes)

    def __repr__(self):
        return f"<Graph (directed={self.directed}, nodes={list(self.nodes.keys())})>"

    # 新增：随机添加不重复的边（之前实现的）
    def add_random_edges(self, num_edges: int):
        """添加指定数量的不重复随机边"""
        import random
        if num_edges <= 0:
            return
        node_indices = list(self.nodes.keys())
        n_nodes = len(node_indices)
        if n_nodes < 2:
            raise ValueError("至少需要两个节点才能添加边")

        if self.directed:
            max_possible = n_nodes * (n_nodes - 1)
        else:
            max_possible = n_nodes * (n_nodes - 1) // 2

        if num_edges > max_possible:
            raise ValueError(f"无法添加 {num_edges} 条边，最大可能为 {max_possible} 条")

        existing_edges = set()
        for u in self.adj:
            for v in self.adj[u]:
                if self.directed:
                    existing_edges.add((u, v))
                else:
                    if u < v:
                        existing_edges.add((u, v))
                    else:
                        existing_edges.add((v, u))

        added = 0
        max_attempts = num_edges * 10
        attempts = 0
        while added < num_edges and attempts < max_attempts:
            u, v = random.sample(node_indices, 2)
            if self.directed:
                edge = (u, v)
            else:
                edge = (u, v) if u < v else (v, u)
            if edge not in existing_edges:
                self.add_edge(u, v)
                existing_edges.add(edge)
                added += 1
            attempts += 1

        if added < num_edges:
            raise RuntimeError(f"尝试 {max_attempts} 次后仍无法找到 {num_edges} 条新边")


def print_edges(graph):
    """
    将图的所有边按 <起点>,<终点> 格式打印。
    无向图只输出一次（起点下标 < 终点下标）。
    有向图输出所有存储的有向边。

    参数:
        graph: Graph 类的实例（需包含 .directed, .adj 属性）
    """
    if graph.directed:
        # 有向图：遍历每个节点的所有邻接点
        for u in sorted(graph.adj.keys()):
            for v in sorted(graph.adj[u]):  # 排序使输出有规律
                print(f"{u},{v}")
    else:
        # 无向图：仅输出 u < v 的边，避免重复
        seen = set()
        for u in sorted(graph.adj.keys()):
            for v in sorted(graph.adj[u]):
                if u < v:
                    print(f"{u} {v}")

# ========== 使用示例 ==========
# if __name__ == "__main__":
    # 创建包含5个节点的无向图，节点值等于下标 (0,1,2,3,4)
    # g = Graph(node_count=5, directed=False)
    # print("初始节点:", list(g.nodes.values()))  # 打印所有节点
    #
    # # 添加一些随机边
    # g.add_random_edges(4)
    # print("邻接关系:", g.adj)
    #
    # # 手动添加一个自定义节点
    # g.add_node(99, "special")
    # g.add_edge(99, 1)
    # print("添加节点后总节点数:", g.adj)
    # print_edges(g)