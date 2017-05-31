import itertools
from inspect import Signature, Parameter

from restpf.utils.helper_functions import to_iterable
from .base import WebFrameworkDriverInterface

from sanic import Sanic
from sanic import response


class SanicDriver(WebFrameworkDriverInterface):

    def __init__(self):
        self.app = Sanic('SanicDriver')
        self.added_endpoints = []

    def _generate_endpoint(self, prefix_path, variables):
        endpoint = '/'.join(itertools.chain(
            prefix_path,
            map(lambda name: f'<{name}>', variables),
        ))
        return '/' + endpoint

    def register_endpoint(self,
                          http_method,
                          endpoint_prefix_path, variables,
                          callback):

        variables = tuple(to_iterable(variables))

        endpoint = self._generate_endpoint(
            endpoint_prefix_path, variables,
        )
        callback = self.callback_wrapper(callback, variables)

        self.app.add_route(callback, endpoint, methods=[http_method.value])
        self.added_endpoints.append(endpoint)

    def remove_all_registered_endpoints(self):
        for endpoint in self.added_endpoints:
            self.app.remove_route(endpoint)

    def callback_wrapper(self, callback, variables):
        variables = to_iterable(variables)

        async def sanic_callback_wrapper(request, **kwargs):
            # status
            # headers: dict.
            # json_body: None or dict.
            status, headers, json_body = await callback(
                # endpoint.
                endpoint_elements=kwargs,
                endpoint_query_strings=request.args,
                # headers,
                headers=request.headers,
                # body.
                json_body=request.json,
                raw_body=request.body,
            )

            return response.json(
                json_body,
                headers=headers,
                status=status,
            )

        parameters = (
            Parameter(name, Parameter.POSITIONAL_OR_KEYWORD)
            for name in itertools.chain(('request',), variables)
        )
        signature = Signature(parameters)
        sanic_callback_wrapper.__signature__ = signature

        return sanic_callback_wrapper

    def create_global_namespace(self):
        pass

    def global_namespace_accessor(self, name):
        pass

    def global_namespace_mutator(self, name, value):
        pass

    def before_server_start(self, name, callback):
        pass

    def run(self, host, port):
        self.app.run(host, port)
