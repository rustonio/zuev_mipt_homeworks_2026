import json
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func: CallableWithMeta[P, R_co], block_time: datetime):
        super().__init__(TOO_MUCH)
        self.func_name = f"{func.__module__}.{func.__name__}"
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int,
        time_to_recover: int,
        triggers_on: type[Exception],
    ):
        errors = []
        if critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on
        self.triggers_count = 0
        self.block_time: datetime | None = None

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R_co:
            self._check_blocked_state(func)
            try:
                result = func(*args, **kwargs)
            except self.triggers_on as exc:
                self._handle_failure(func, exc)
                raise
            else:
                self._reset_state()
            return result

        return wrapper

    def _check_blocked_state(self, func: CallableWithMeta[P, R_co]) -> None:
        block_time = self.block_time
        if block_time is None:
            return
        now = datetime.now(UTC)
        if (now - block_time).total_seconds() < self.time_to_recover:
            raise BreakerError(func, block_time)
        self._reset_state()

    def _reset_state(self) -> None:
        self.block_time = None
        self.triggers_count = 0

    def _handle_failure(self, func: CallableWithMeta[P, R_co], exc: Exception) -> None:
        self.triggers_count += 1
        if self.triggers_count >= self.critical_count:
            self.block_time = datetime.now(UTC)
            raise BreakerError(func, self.block_time) from exc


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
