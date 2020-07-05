from privex.helpers import PrivexException, empty_if


class MyAppException(PrivexException):
    pass


class APIAlreadyRegistered(MyAppException):
    pass


class APIException(MyAppException):
    """

    It's recommended to add an error code using :func:`.add_app_error`, allowing you to raise just the error code, with the message + status
    automatically getting filled out.

        >>> from postfixparser.core import add_app_error
        >>> add_app_error('INV_USERNAME', "Username must be at least 5 characters", 400)

    Then, in your API view, simply raise :class:`.APIException` and the error handler :func:`.api_exception_handler` will automatically
    output the error in raw JSON or human friendly HTML depending on how the API is being queried.

        >>> async def my_api_view():
        >>>     if len(request.values['username']) < 5:
        >>>         raise APIException("INV_USERNAME")

    The above example would result in an error returned like this::

        GET /api/v1/my_api_view HTTP/1.1

        HTTP/1.1 400 Bad Request

        {
            "error": true,
            "error_code": "INV_USERNAME",
            "message": "Username must be at least 5 characters",
            "result": null
        }


    """
    
    def __init__(self, error_code="UNKNOWN_ERROR", message: str = None, status: int = None, template: str = None, extra: dict = None):
        from .core import _get_error
        _err = _get_error(error_code)
        super().__init__(error_code + ' ' + empty_if(message, _err.message))
        self.message = message
        self.error_code = error_code
        self.status = empty_if(status, _err.status, zero=True)
        self.template = template
        self.extra = {} if extra is None else extra

