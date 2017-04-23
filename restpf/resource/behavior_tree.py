"""
classes:

- BehaviorTreeRoot
- BehaviorTreeNode

BehaviorTreeRoot is a special case of BehaviorTreeNode.
"""


class classproperty:

    def __init__(self, f):
        self._f = f

    def __get__(self, obj, owner):
        return self._f(owner)


class BehaviorTreeNode:

    def __init__(self):
        self._bh_name = type(self).__name__.lower()

        self._bh_root = None
        self._bh_parent = None

        self._bh_children = []
        self._bh_named_children = {}

    def bh_rename(self, name):
        self._bh_name = name

    def bh_add_child(self, child):
        assert isinstance(child, BehaviorTreeNode)

        child._bh_parent = self
        child._bh_root = self._bh_root

        self._bh_children.append(child)
        self._bh_named_children[child._bh_name] = child

    @property
    def bh_children(self):
        return self._bh_children

    @property
    def bh_children_size(self):
        return len(self._bh_children)

    def bh_child(self, idx=0):
        return self._bh_children[idx]

    def bh_named_child(self, name):
        return self._bh_named_children.get(name)


class BehaviorTreeRoot(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self._bh_root = self


class BehaviorTreeNodeState(BehaviorTreeNode):

    BH_NODECLS = None

    def __init__(self):
        super().__init__()
        self._bh_node = None

    def bh_bind_node(self, node):
        assert issubclass(self.BH_NODECLS, BehaviorTreeNode)
        assert type(node) is self.BH_NODECLS

        self._bh_node = node
        self.bh_rename(node._bh_name)

    @property
    def bh_node(self):
        return self._bh_node

    @classproperty
    def bh_nodecls(cls):
        return cls.BH_NODECLS

    def bh_relative_node(self, *names):
        node = self._bh_node
        for name in names:
            node = node.bh_named_child(name)
            if node is None:
                raise "cannot find name: " + name
        return node

    def bh_relative_nodecls(self, *names):
        node = self.bh_relative_node(*names)
        return type(node)


class BehaviorTreeNodeStateLeaf(BehaviorTreeNodeState):

    def _set_bh_value(self, value):
        self._bh_value = value

    def _get_bh_value(self):
        return self._bh_value

    bh_value = property(_get_bh_value, _set_bh_value)


class BehaviorTreeNodeStateNested(BehaviorTreeNodeState):
    pass
