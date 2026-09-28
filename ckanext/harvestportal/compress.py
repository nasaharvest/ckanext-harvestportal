from flask import request
from flask_compress import Compress


class HarvestportalCompress(Compress):
    def after_request(self, response):
        # Datastore dumps are streamed and can be gigabytes; compressing them
        # on the fly would hold a uWSGI worker for the whole transfer.
        if request.endpoint and request.endpoint.startswith("datastore."):
            return response
        return super().after_request(response)


def init_compress(app):
    # Brotli is about twice as fast as gzip for the same output size on our
    # assets; gzip/deflate remain as fallbacks. Streamed responses (static
    # files) can't use gzip in Flask-Compress, hence the separate list.
    app.config.setdefault("COMPRESS_ALGORITHM", ["br", "gzip"])
    app.config.setdefault("COMPRESS_ALGORITHM_STREAMING", ["br", "deflate"])
    app.config.setdefault("COMPRESS_BR_LEVEL", 4)
    HarvestportalCompress(app)
    return app
