# ==============================================================================
#
# Client (HTTP-client)
#
# This file was generated by a code generator.
# Don't make changes to it manually.
#
# ==============================================================================

# jinja2: lstrip_blocks: "True"
# mypy: ignore-errors

from __future__ import annotations

import abc

from datetime import datetime
from datetime import date

from httpx import Timeout
from typing import Literal
from typing import Any
from typing import Optional
from typing import Union
from typing import Callable
from typing import get_type_hints
from typing import Mapping
from typing import Sequence
from typing import IO
from typing import cast

from jaeger_client import Tracer
from jaeger_client.span import Span
from opentracing.propagation import Format

from prometheus_client import Counter
from prometheus_client import Histogram

import httpx
from pydantic import BaseModel
from pydantic import Field
from pydantic import root_validator
from pydantic import validator
from pydantic import HttpUrl
import logging
from functools import wraps
from opentracing.ext import tags


tracer: Tracer


class TracerNotConfigured(Exception):
    pass


class TracerConfig(BaseModel):
    app_name: str
    host: str
    port: int
    propagation: str
    jaeger_enabled: bool


class BaseTracerIntegration(abc.ABC):
    def __init__(self, tracer: Optional[Tracer] = None):
        self.tracer = tracer

    @abc.abstractmethod
    def get_tracing_http_headers(self) -> dict[str, str]: ...

    @abc.abstractmethod
    def get_current_trace_id(self) -> Optional[str]: ...

    @abc.abstractmethod
    def get_tracer(self) -> Tracer: ...

    @abc.abstractmethod
    def get_current_span(self) -> Optional[Span]: ...


class DefaultTracerIntegration(BaseTracerIntegration):
    def get_tracing_http_headers(self) -> dict[str, str]:
        tracer = self.get_tracer()
        span = self.get_current_span()
        if not span:
            return {}
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
        headers: dict[str, str] = {}
        tracer.inject(span, Format.HTTP_HEADERS, headers)
        return headers

    def get_current_trace_id(self) -> Optional[str]:
        span = self.get_current_span()
        trace_id = span.trace_id if span else None
        return '{:x}'.format(trace_id) if trace_id else None

    def get_tracer(self) -> Tracer:
        if not self.tracer:
            raise TracerNotConfigured('configure tracing first')
        return self.tracer

    def get_current_span(self) -> Optional[Span]:
        tracer = self.get_tracer()
        active = tracer.scope_manager.active
        return cast(Span, active.span) if active else None


def tracing(f: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(f)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not self.tracer_integration:
            return await f(self, *args, **kwargs)

        db_query = kwargs.get('query', None)
        current_tags = {}
        if db_query is not None:
            current_tags[tags.DATABASE_TYPE] = 'postgres'
            current_tags[tags.DATABASE_STATEMENT] = db_query

        tracer = self.tracer_integration.get_tracer()
        span = tracer.start_span(operation_name=f.__qualname__, child_of=self.tracer_integration.get_current_span(), tags=current_tags)
        scope = tracer.scope_manager.activate(span, True)
        try:
            result = await f(self, *args, **kwargs)
        except Exception as exp:
            span.set_tag(tags.ERROR, True)
            span.set_tag('error.message', str(exp))
            raise exp
        finally:
            scope.close()
        return result

    return wrapper

# backward compatibility for httpx<0.18.2
try:
    DEFAULT_AUTH = httpx.USE_CLIENT_DEFAULT
except AttributeError:
    DEFAULT_AUTH = None


class BaseMetricsIntegration(abc.ABC):
    def __init__(
        self,
        client_response_time_histogram: Optional[Histogram] = None,
        client_non_http_errors_counter: Optional[Counter] = None,
    ):
        self._client_response_time_histogram = client_response_time_histogram
        self._client_non_http_errors_counter = client_non_http_errors_counter

    @abc.abstractmethod
    def on_request_error(self) -> None: ...

    @abc.abstractmethod
    def on_request_success(self) -> None: ...


class DefaultMetricsIntegration(BaseMetricsIntegration):
    def on_request_error(self, error: Exception) -> None:
        self._client_non_http_errors_counter.labels(
            client_name='',
            http_method='',
            http_target='',
            exception=error.__class__.__name__,
        ).inc(1)
        raise error

    def on_request_success(self, response) -> None:
        self._client_response_time_histogram.labels(
            client_name='',
            http_method='',
            http_target='',
            http_status_code=response.status_code,
        ).observe(response.elapsed.total_seconds())


FileContent = Union[IO[str], IO[bytes], str, bytes]
FileTypes = Union[
    # file (or text)
    FileContent,
    # (filename, file (or text))
    tuple[Optional[str], FileContent],
    # (filename, file (or text), content_type)
    tuple[Optional[str], FileContent, Optional[str]],
]

class EmptyBody(BaseModel):
    status_code: int
    text: str


class BaseObjectResp(BaseModel):
    string_data: str

    @validator("string_data", pre=True)
    def check(cls, v: str) -> str:
        type_hints = get_type_hints(cls)
        string_data_values: tuple[str] = type_hints["string_data"].__dict__['__args__']

        if v not in string_data_values:
            raise ValueError(f'invalid string_data for {cls}')

        return v


class GetBinaryResponse200(BaseModel):
    """
    None
    """

    # required ---

    # optional ---
    content: Optional[bytes] = None


class GetTextResponse200(BaseModel):
    """
    None
    """

    # required ---

    # optional ---
    text: Optional[str] = None


class GetListobjectsResponse200(BaseModel):
    """
    None
    """

    # required ---

    # optional ---


class AllOfRefObj(BaseModel):
    """
    All Of
    """

    # required ---

    # optional ---
    id: Optional[str] = None
    data: Optional[int] = None


class TestSafetyKey(BaseModel):
    """
    model for testing safety key
    """

    # required ---

    # optional ---
    for_: Optional[str] = Field(description="reserved word, expecting \"for_\"", alias="for")
    class_: Optional[str] = Field(description="reserved word, expecting \"class_\"", alias="class")
    with_dot_and_hyphens: Optional[int] = Field(description="invalid identifier, expecting \"with_dot_and_hyphens\"", alias="33with.dot-and-hyphens&*")
    old_feature_priority: Optional[int] = Field(description="__safety_key__(old_feature_priority) invalid identifier, expecting \"old_feature_priority\"", alias="34with.dot-and-hyphens&*")

    class Config:
        # Обращение по имени поля, даже если есть алиас.
        allow_population_by_field_name = True

    @root_validator
    def change_name(cls, values):
        """
        Каст полей согласно алиасам

        В OpenApi-спеке названия полей могут быть в формате, в котором
        нельзя создавать имена переменных в python, они заменяются безопасными алиасами
        """
        values["for"] = values["for_"]
        del values["for_"]
        
        values["class"] = values["class_"]
        del values["class_"]
        
        values["33with.dot-and-hyphens&*"] = values["with_dot_and_hyphens"]
        del values["with_dot_and_hyphens"]
        
        values["34with.dot-and-hyphens&*"] = values["old_feature_priority"]
        del values["old_feature_priority"]
        
        return values


class UnknownError(BaseModel):
    """
    UnknownError
    """

    # required ---

    # optional ---
    code: Optional[str] = None


class DeleteObjectResp(BaseModel):
    """
    DeleteObjectResp
    """

    # required ---

    # optional ---
    status: Optional[str] = None


class PutObjectResp(BaseModel):
    """
    PutObjectResp
    """

    # required ---

    # optional ---
    status: Optional[str] = None


class PatchObjectResp(BaseModel):
    """
    PatchObjectResp
    """

    # required ---

    # optional ---
    status: Optional[str] = None


class PostObjectResp(BaseModel):
    """
    PostObjectResp
    """

    # required ---

    # optional ---
    status: Optional[str] = None


class PostFile(BaseModel):
    """
    PostFile
    """

    # required ---
    text: str

    # optional ---


class PutObjectData(BaseModel):
    """
    PutObjectData
    """

    # required ---
    id: str
    data: int

    # optional ---


class PatchObjectData(BaseModel):
    """
    PatchObjectData
    """

    # required ---
    id: str
    data: int

    # optional ---


class PostObjectData(BaseModel):
    """
    PostObjectData
    """

    # required ---
    string_data: str
    integer_data: int
    array_data: list[str]
    boolean_data: bool
    event_data: dict = Field(description="__safety_key__(event_data)", alias="event-data")

    # optional ---
    date: Optional[date] = None
    datetime: Optional[datetime] = None
    url: Optional[HttpUrl] = None

    class Config:
        # Обращение по имени поля, даже если есть алиас.
        allow_population_by_field_name = True

    @root_validator
    def change_name(cls, values):
        """
        Каст полей согласно алиасам

        В OpenApi-спеке названия полей могут быть в формате, в котором
        нельзя создавать имена переменных в python, они заменяются безопасными алиасами
        """
        values["event-data"] = values["event_data"]
        del values["event_data"]
        
        return values


class GetObjectResp(BaseModel):
    """
    GetObjectResp
    """

    # required ---

    # optional ---
    string_data: Optional[str] = Field(description="String Data. [__discriminator__(BaseObjectResp.string_data)]")
    integer_data: Optional[int] = None
    array_data: Optional[list[str]] = None
    boolean_data: Optional[bool] = None


class Data(BaseModel):
    """
    Data
    """

    # required ---

    # optional ---
    id: Optional[str] = None
    data: Optional[int] = None


class AllOfResp(BaseModel):
    """
    All Of Resp
    """

    # required ---

    # optional ---
    all_of: Optional[AllOfRefObj] = None


class BasicAuth(BaseModel):
        username: str
        password: str


class Client:
    def __init__(
        self,
        base_url: str,
        timeout: int = 5,
        client: Optional[httpx.AsyncClient] = None,
        headers: dict[str, str] = None,
        tracer_integration: Optional[BaseTracerIntegration] = None,
        metrics_integration: Optional[BaseMetricsIntegration] = None,
    ):
        self.client = client or httpx.AsyncClient(timeout=Timeout(timeout))
        self.base_url = base_url
        self.headers = headers or {}
        self.tracer_integration = tracer_integration
        self.metrics_integration=metrics_integration
    @tracing
    async def get_object(
        self,
        object_id: str,
        from_: str,
        return_error: Optional[str] = None,
        auth: Optional[BasicAuth] = None,
    ) -> Union[GetObjectResp, UnknownError]:
        url = self._get_url(f'/objects/{object_id}')

        params = {
            'from': from_,
        }
        if return_error is not None:
            params['return_error'] = return_error

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        try:
            response = await self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return GetObjectResp.parse_obj(response.json())

        if response.status_code == 500:
            client_name = ""
            method = "get"
            if response.content is None:
                content = None
            else:
                content = response.content[:500]

            self.log_error(client_name, method, url, params, content, headers_)

            return UnknownError.parse_obj(response.json())
    
    @tracing
    async def get_list_objects(
        self,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[list[GetObjectResp]]:
        url = self._get_url(f'/objects')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        try:
            response = await self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return [GetObjectResp.parse_obj(item) for item in response.json()]
    
    @tracing
    async def get_text(
        self,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[GetTextResponse200]:
        url = self._get_url(f'/text')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        try:
            response = await self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return GetTextResponse200(text=response.text)
    
    @tracing
    async def get_empty(
        self,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[EmptyBody]:
        url = self._get_url(f'/empty')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        try:
            response = await self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return EmptyBody(status_code=response.status_code, text=response.text)
    
    @tracing
    async def get_binary(
        self,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[GetBinaryResponse200]:
        url = self._get_url(f'/binary')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        try:
            response = await self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return GetBinaryResponse200(content=response.content)
    
    @tracing
    async def get_allof(
        self,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[AllOfResp]:
        url = self._get_url(f'/allof')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        try:
            response = await self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return AllOfResp.parse_obj(response.json())
    
    @tracing
    async def get_object_slow(
        self,
        object_id: str,
        return_error: Optional[str] = None,
        auth: Optional[BasicAuth] = None,
    ) -> Union[GetObjectResp, UnknownError]:
        url = self._get_url(f'/slow/objects/{object_id}')

        params = {
        }
        if return_error is not None:
            params['return_error'] = return_error

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        try:
            response = await self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return GetObjectResp.parse_obj(response.json())

        if response.status_code == 500:
            client_name = ""
            method = "get"
            if response.content is None:
                content = None
            else:
                content = response.content[:500]

            self.log_error(client_name, method, url, params, content, headers_)

            return UnknownError.parse_obj(response.json())
    
    @tracing
    async def post_object_without_body(
        self,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[PostObjectResp]:
        url = self._get_url(f'/post-without-body')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        try:
            response = await self.client.post(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return PostObjectResp.parse_obj(response.json())
    
    @tracing
    async def post_object(
        self,
        body: Optional[Union[PostObjectData, dict[str, Any]]] = None,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[PostObjectResp]:
        url = self._get_url(f'/objects')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        if isinstance(body, dict):
            json = body
        elif isinstance(body, PostObjectData):
            json = body.dict()
        else:
            json = None
        
        try:
            response = await self.client.post(url, json=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return PostObjectResp.parse_obj(response.json())
    
    @tracing
    async def post_form_object(
        self,
        body: Optional[Union[PostObjectData, dict[str, Any]]] = None,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[PostObjectResp]:
        url = self._get_url(f'/objects-form-data')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        if isinstance(body, dict):
            json = body
        elif isinstance(body, PostObjectData):
            json = body.dict()
        else:
            json = None
        
        headers_.update({'Content-Type': 'application/x-www-form-urlencoded'})
        try:
            response = await self.client.post(url, data=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return PostObjectResp.parse_obj(response.json())
    
    @tracing
    async def post_multipart_form_data(
        self,
        body: Optional[Union[PostFile, dict[str, Any]]] = None,
        auth: Optional[BasicAuth] = None,
        files: Optional[Union[Mapping[str, FileTypes], Sequence[tuple[str, FileTypes]]]] = None,
    ) -> Optional[PostObjectResp]:
        url = self._get_url(f'/multipart-form-data')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        if isinstance(body, dict):
            json = body
        elif isinstance(body, PostFile):
            json = body.dict()
        else:
            json = None
        
        # Content-Type=multipart/form-data doesn't work, because header MUST contain boundaries
        # let library do it for us
        headers_.pop("Content-Type", None)
        
        try:
            response = await self.client.post(url, data=json, headers=headers_, params=params, auth=auth_, files=files)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return PostObjectResp.parse_obj(response.json())
    
    @tracing
    async def patch_object(
        self,
        object_id: str,
        body: Optional[Union[PatchObjectData, dict[str, Any]]] = None,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[PatchObjectResp]:
        url = self._get_url(f'/objects/{object_id}')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        if isinstance(body, dict):
            json = body
        elif isinstance(body, PatchObjectData):
            json = body.dict()
        else:
            json = None
        
        try:
            response = await self.client.patch(url, json=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return PatchObjectResp.parse_obj(response.json())
    
    @tracing
    async def put_object(
        self,
        object_id: str,
        body: Optional[Union[PutObjectData, dict[str, Any]]] = None,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[PutObjectResp]:
        url = self._get_url(f'/objects/{object_id}')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        if isinstance(body, dict):
            json = body
        elif isinstance(body, PutObjectData):
            json = body.dict()
        else:
            json = None
        
        try:
            response = await self.client.put(url, json=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return PutObjectResp.parse_obj(response.json())
    
    @tracing
    async def put_object_slow(
        self,
        object_id: str,
        body: Optional[Union[PutObjectData, dict[str, Any]]] = None,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[PutObjectResp]:
        url = self._get_url(f'/slow/objects/{object_id}')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        if isinstance(body, dict):
            json = body
        elif isinstance(body, PutObjectData):
            json = body.dict()
        else:
            json = None
        
        try:
            response = await self.client.put(url, json=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return PutObjectResp.parse_obj(response.json())
    
    @tracing
    async def delete_object(
        self,
        object_id: str,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[DeleteObjectResp]:
        url = self._get_url(f'/objects/{object_id}')

        params = {
        }

        headers_ = self.headers.copy()

        if self.tracer_integration:
            self.add_tracing_data_to_headers(headers_)

        if auth is None:
            auth_ = DEFAULT_AUTH
        elif isinstance(auth, httpx.Auth):
            auth_ = auth
        else:
            auth_ = (auth.username, auth.password)
        
        try:
            response = await self.client.delete(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(exc)
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(response)

        if response.status_code == 200:
            return DeleteObjectResp.parse_obj(response.json())
    
    
    async def close(self) -> None:
        await self.client.aclose()

    def _get_url(self, path: str) -> str:
        return f'{self.base_url}{path}'

    def log_extra(self, **kwargs: Any) -> dict[str, Any]:
        return {'extra': {'props': {'data': kwargs}}}

    def log_error(self, client_name: str, method, url: str, params, content, headers) -> None:
        msg = f"request error"
        msg += f" | client={client_name}"
        msg += f" | method={method}"
        msg += f" | {url=}"
        msg += f" | {params=}"
        msg += f" | content={content}"
        msg += f" | headers={headers}"

        logging.error(
            msg,
            **self.log_extra(
                client=client_name,
                method=method,
                content=content,
                url=url,
                params=params,
            ),
        )

    def add_tracing_data_to_headers(self, headers_: dict[str, str]) -> None:
        tracing_headers = self.tracer_integration.get_tracing_http_headers()
        headers_.update(tracing_headers)
        trace_id = self.tracer_integration.get_current_trace_id() or ''
        headers_['x-trace-id'] = trace_id


GetBinaryResponse200.update_forward_refs()
GetTextResponse200.update_forward_refs()
GetListobjectsResponse200.update_forward_refs()
AllOfRefObj.update_forward_refs()
TestSafetyKey.update_forward_refs()
UnknownError.update_forward_refs()
DeleteObjectResp.update_forward_refs()
PutObjectResp.update_forward_refs()
PatchObjectResp.update_forward_refs()
PostObjectResp.update_forward_refs()
PostFile.update_forward_refs()
PutObjectData.update_forward_refs()
PatchObjectData.update_forward_refs()
PostObjectData.update_forward_refs()
GetObjectResp.update_forward_refs()
Data.update_forward_refs()
AllOfResp.update_forward_refs()
