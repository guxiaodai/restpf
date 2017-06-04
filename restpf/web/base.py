'''
Defines the interfaces of web framework engine.

- Endpoint registration.
    - Rounting (variable in path, http method).
    - Registration clean up (mainly for testing).
- I/O abstraction.
    - Input: headers, json body, raw body.
    - Output: headers, json body.
- Global namespace.
    - Read/Write to global namespace.
- Operation hooks.
    - Framework begin.
    - Framework end.
    - Per-request begin.
    - Per-request end.
'''


class RestPFGlobalNamespace:

    @classmethod
    def register_namespace_operator(cls, namespace_operator):
        cls._namespace_operator = namespace_operator

    @classmethod
    def unregister_namespace_operator(cls):
        cls._namespace_operator = None

    @classmethod
    def get(cls, name):
        if cls._namespace_operator is None:
            return None
        return cls._namespace_operator.global_namespace_accessor(name)

    @classmethod
    def set(cls, name, value):
        cls._namespace_operator.global_namespace_mutator(name, value)


# TODO: review the interface design.
class WebFrameworkDriverInterface:

    def register_endpoint(self,
                          http_method,
                          endpoint_prefix_path, variables,
                          callback):
        pass

    def remove_all_registered_endpoints(self):
        pass

    def callback_wrapper(self, callback, variables):
        pass

    def create_global_namespace(self):
        pass

    def global_namespace_accessor(self, name):
        pass

    def global_namespace_mutator(self, name, value):
        pass

    def before_server_start(self, name, value_or_callback):
        pass

    def run(self, host, port):
        pass
