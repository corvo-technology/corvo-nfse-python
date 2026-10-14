from corvo_nfse import CorvoApiError


def test_fields() -> None:
    err = CorvoApiError(status=400, code="ERROR_VALIDATION", message="bad payload")
    assert err.status == 400
    assert err.code == "ERROR_VALIDATION"
    assert err.message == "bad payload"
    assert err.details == []
    assert err.request_id is None
    assert err.retry_after is None


def test_defaults() -> None:
    err = CorvoApiError(status=500, code="http_500", message="")
    assert err.details == []
    assert err.request_id is None
    assert err.retry_after is None


def test_details_and_request_id() -> None:
    err = CorvoApiError(
        status=422,
        code="ERROR_VALIDATION",
        message="invalid",
        details=[{"field": "amount", "code": "invalid", "message": "must be > 0"}],
        request_id="req_123",
        retry_after=30,
    )
    assert err.details[0]["field"] == "amount"
    assert err.request_id == "req_123"
    assert err.retry_after == 30


def test_is_exception_and_stringifies() -> None:
    err = CorvoApiError(status=0, code="network_error", message="boom")
    assert isinstance(err, Exception)
    assert str(err) == "boom"


def test_raiseable() -> None:
    try:
        raise CorvoApiError(status=404, code="http_404", message="nope")
    except CorvoApiError as caught:
        assert caught.code == "http_404"
        assert caught.status == 404
