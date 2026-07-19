"""Shared HTTP helpers for the ``requests``-based data-fetch scripts.

Most non-DataMiner2 fetchers (EIA, MISO, data.gov, …) hand-roll the same
``requests.Session`` with a retry/back-off adapter. :func:`retrying_session`
homes that once and :func:`download` is a one-shot GET on top of it.

Agent-proxy CA behavior is **preserved, never disabled**: outbound HTTPS goes
through the environment's agent proxy, and ``requests`` picks up the proxy
(``HTTPS_PROXY``) and the CA bundle (``REQUESTS_CA_BUNDLE`` / ``CURL_CA_BUNDLE``,
pointing at ``/root/.ccr/ca-bundle.crt``) from the environment automatically.
Nothing here sets ``verify=False`` or clears those variables; callers must not
either (see the repo's proxy README).

The PJM DataMiner2 feeds use their own ``urllib``-based client
(:mod:`scripts.lib.pjm_dataminer`) because they page with a subscription-key
header rather than a plain retrying GET; this module is for everything else.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_RETRIES = 4
DEFAULT_BACKOFF = 1.5
DEFAULT_STATUS_FORCELIST = (429, 500, 502, 503, 504)


def retrying_session(
    *,
    retries: int = DEFAULT_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF,
    status_forcelist: tuple[int, ...] = DEFAULT_STATUS_FORCELIST,
    user_agent: str = "market-sim/fetch",
) -> requests.Session:
    """Return a ``requests.Session`` with retry/back-off on both HTTP schemes.

    The session honours the environment's agent proxy and CA bundle (it does not
    touch ``verify``). ``backoff_factor`` follows urllib3's schedule
    (``backoff_factor * 2**(attempt-1)`` seconds between tries).

    Args:
        retries: total retries per request.
        backoff_factor: urllib3 back-off base.
        status_forcelist: HTTP statuses that trigger a retry.
        user_agent: the ``User-Agent`` header set on the session.

    Returns:
        A configured :class:`requests.Session`.
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset({"GET", "POST"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": user_agent})
    return session


def download(
    url: str,
    *,
    session: requests.Session | None = None,
    timeout: float = 120,
    **kwargs,
) -> requests.Response:
    """GET ``url`` with retries; return the response, raising on a final error.

    Uses ``session`` if given (so callers can reuse one connection pool),
    otherwise a fresh :func:`retrying_session`. Extra keyword arguments pass
    through to :meth:`requests.Session.get` (``params``, ``headers``, ``stream``,
    …). Never disables TLS verification.
    """
    sess = session or retrying_session()
    resp = sess.get(url, timeout=timeout, **kwargs)
    resp.raise_for_status()
    return resp
