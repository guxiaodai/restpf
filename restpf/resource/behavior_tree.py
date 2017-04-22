"""
classes:

- BehaviorTreeRoot
- BehaviorTreeNode

BehaviorTreeRoot is a special case of BehaviorTreeNode.
"""


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
    def bh_child_size(self):
        return len(self._bh_children)

    def bh_child(self, idx=0):
        return self._bh_children[idx]

    def bh_named_child(self, name):
        return self._bh_named_children.get(name)

    # def bh_create_state_tree(self, to_statecls):
    #     nodecls = type(self)

    #     statecls = to_statecls.get(nodecls)
    #     if statecls is None:
    #         raise "cannot find corresponding class"

    #     state = statecls(self, to_statecls)
    #     # only reasonable for dict type.
    #     if issubclass(statecls, BehaviorTreeNodeStateDictValue):
    #         for child_node in self._bh_children:
    #             child_state = child_node.create_state_tree(to_statecls)
    #             state.add_bh_child(child_state)

    #     return state


class BehaviorTreeRoot(BehaviorTreeNode):

    def __init__(self):
        super().__init__()
        self._bh_root = self


class BehaviorTreeNodeState(BehaviorTreeNode):

    def __init__(self, node, to_statecls):
        super().__init__()

        assert isinstance(node, BehaviorTreeNode)
        self._bh_node = node
        self._bh_to_statecls = to_statecls

    # def __getattr__(self, name):
    #     obj = getattr(self._bh_node, name)
    #     if not callable(obj):
    #         # access constant.
    #         return obj
    #     else:
    #         # bind to method (operation) defined in tree structure.
    #         return functools.partial(obj, self)

    def bh_get_nodecls(self, *names):
        node = self._bh_node
        for name in names:
            node = node.bh_named_child(name)
            if node is None:
                raise "cannot find name: " + name

        return type(node)

    def bh_get_statecls(self, *names):
        nodecls = self.bh_get_nodecls(*names)
        return self._bh_to_statecls[nodecls]

    def bh_create_state(self, *names):
        statecls = self.bh_get_statecls(*names)
        return statecls(self._bh_node, self._bh_to_statecls)


class BehaviorTreeNodeStateLeaf(BehaviorTreeNodeState):

    def _set_bh_value(self, value):
        self._bh_value = value

    def _get_bh_value(self):
        return self._bh_value

    bh_value = property(_get_bh_value, _set_bh_value)


class BehaviorTreeNodeStateNested(BehaviorTreeNodeState):
    pass
