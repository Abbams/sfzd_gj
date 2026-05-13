class TreeNode:
    """树节点类"""
    def __init__(self, value):
        self.value = value          # 节点存储的数据
        self.children = []          # 子节点列表

    def add_child(self, child_node):
        """添加子节点"""
        self.children.append(child_node)

    def remove_child(self, child_node):
        """移除指定的子节点（如果存在）"""
        if child_node in self.children:
            self.children.remove(child_node)
            return True
        return False

    def __repr__(self):
        return f"TreeNode({self.value})"


class Tree:
    """树结构（多叉树）"""
    def __init__(self, root_value=None):
        """
        初始化树，可指定根节点的值
        若不指定，则创建空树（根为 None）
        """
        self.root = TreeNode(root_value) if root_value is not None else None

    def is_empty(self):
        """判断树是否为空"""
        return self.root is None

    def set_root(self, value):
        """设置根节点（如果树为空）"""
        if self.is_empty():
            self.root = TreeNode(value)
        else:
            raise ValueError("树已有根节点，不能重新设置根")

    def add_child(self, parent_node, child_value):
        """
        为指定父节点添加一个值为 child_value 的子节点
        若 parent_node 不是树中的节点，则不会添加
        """
        if parent_node is None:
            raise ValueError("父节点不能为 None")
        child_node = TreeNode(child_value)
        parent_node.add_child(child_node)
        return child_node

    def remove_node(self, node, parent=None):
        """
        删除节点（及其所有子节点）
        需要提供节点本身及其父节点（以便从父节点的 children 中移除）
        若 parent 为 None，表示要删除根节点
        """
        if node is None:
            return False
        if parent is None:
            # 删除根节点
            self.root = None
            return True
        else:
            return parent.remove_child(node)

    def find_node(self, value, node=None):
        """
        查找值为 value 的节点（返回第一个匹配的节点）
        若未找到返回 None
        """
        if node is None:
            node = self.root
        if node is None:
            return None
        if node.value == value:
            return node
        for child in node.children:
            result = self.find_node(value, child)
            if result:
                return result
        return None

    def get_height(self, node=None):
        """
        获取树的高度（从指定节点开始，若 node 为 None 则从根开始）
        高度定义为从该节点到最远叶子节点的边数
        """
        if node is None:
            node = self.root
        if node is None or not node.children:
            return 0
        return 1 + max(self.get_height(child) for child in node.children)

    def preorder(self, node=None, visit=None):
        """
        前序遍历（根 -> 左 -> 右，此处为根 -> 子节点依次）
        visit 为可选的访问函数，若未提供则打印节点值
        """
        if node is None:
            node = self.root
        if node is None:
            return
        if visit is None:
            print(node.value, end=' ')
        else:
            visit(node)
        for child in node.children:
            self.preorder(child, visit)

    def postorder(self, node=None, visit=None):
        """
        后序遍历（子节点 -> 根）
        """
        if node is None:
            node = self.root
        if node is None:
            return
        for child in node.children:
            self.postorder(child, visit)
        if visit is None:
            print(node.value, end=' ')
        else:
            visit(node)

    def level_order(self, visit=None):
        """
        层序遍历（广度优先）
        """
        if self.root is None:
            return
        from collections import deque
        queue = deque([self.root])
        while queue:
            node = queue.popleft()
            if visit is None:
                print(node.value, end=' ')
            else:
                visit(node)
            queue.extend(node.children)

    def __repr__(self):
        return f"Tree(root={self.root})"


# ------------------- 示例用法 -------------------
if __name__ == "__main__":
    # 创建树并设置根节点
    tree = Tree("根节点")
    print("初始树:", tree)