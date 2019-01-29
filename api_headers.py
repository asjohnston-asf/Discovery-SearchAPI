from werkzeug.datastructures import Headers


def base(mimetype):
    base_headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-type': mimetype
    }

    headers = Headers()

    for name, value in base_headers.items():
        headers.add(name, value)

    return headers
