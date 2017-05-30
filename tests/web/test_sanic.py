import json

from restpf.utils.constants import HTTPMethodConfig
from restpf.web.sanic import SanicDriver


def test_basic_usage():
    driver = SanicDriver()

    async def test_callback(endpoint_elements,
                            endpoint_query_strings,
                            headers,
                            json_body,
                            raw_body):

        assert '2' == endpoint_elements['whatever_id']
        return 200, {}, {'result': 42}

    driver.register_endpoint(
        HTTPMethodConfig.GET,
        ['foo', 'bar'], ['whatever_id'],
        test_callback,
    )

    _, response = driver.app.test_client.get('/foo/bar/2')
    assert 200 == response.status
    assert 42 == json.loads(response.text)['result']
