"""
Defines classes for building resource structure.

Example:

foo = Resource(
    'foo',
    Attributes(
        Boolean('normal_user'),
        String('username'),
        ...
    ),
    Relationships(
        ...
    ),
})

foo.noraml_user
foo.username
"""


class ResourceDefinition:

    def __init__(self, resource_type, *option_containers):
        self.resource_type = resource_type
