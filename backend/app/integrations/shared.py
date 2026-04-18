import httpx


def build_async_client(
    *,
    base_url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        headers=headers or {},
        timeout=timeout,
    )


def build_sync_client(
    *,
    base_url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> httpx.Client:
    return httpx.Client(
        base_url=base_url,
        headers=headers or {},
        timeout=timeout,
    )
