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
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from typing import List
from typing import Tuple
from typing import Any
from typing import Dict
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
    def get_tracing_http_headers(self) -> Dict[str, str]: ...

    @abc.abstractmethod
    def get_current_trace_id(self) -> Optional[str]: ...

    @abc.abstractmethod
    def get_tracer(self) -> Tracer: ...

    @abc.abstractmethod
    def get_current_span(self) -> Optional[Span]: ...


class DefaultTracerIntegration(BaseTracerIntegration):
    def get_tracing_http_headers(self) -> Dict[str, str]:
        tracer = self.get_tracer()
        span = self.get_current_span()
        if not span:
            return {}
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_CLIENT)
        headers: Dict[str, str] = {}
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
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not self.tracer_integration:
            return f(self, *args, **kwargs)

        db_query = kwargs.get('query', None)
        current_tags = {}
        if db_query is not None:
            current_tags[tags.DATABASE_TYPE] = 'postgres'
            current_tags[tags.DATABASE_STATEMENT] = db_query

        tracer = self.tracer_integration.get_tracer()
        span = tracer.start_span(operation_name=f.__qualname__, child_of=self.tracer_integration.get_current_span(), tags=current_tags)
        scope = tracer.scope_manager.activate(span, True)
        try:
            result = f(self, *args, **kwargs)
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
    def on_request_error(self, client_name: str, error: Exception, http_method: str, http_target: str) -> None: ...

    @abc.abstractmethod
    def on_request_success(self, client_name: str, response, http_method: str, http_target: str) -> None: ...


class DefaultMetricsIntegration(BaseMetricsIntegration):
    def on_request_error(self, client_name: str, error: Exception, http_method: str, http_target: str) -> None:
        self._client_non_http_errors_counter.labels(
            client_name=client_name,
            http_method=http_method,
            http_target=http_target,
            exception=error.__class__.__name__,
        ).inc(1)
        raise error

    def on_request_success(self, client_name: str, response, http_method: str, http_target: str) -> None:
        self._client_response_time_histogram.labels(
            client_name=client_name,
            http_method=http_method,
            http_target=http_target,
            http_status_code=response.status_code,
        ).observe(response.elapsed.total_seconds())


FileContent = Union[IO[str], IO[bytes], str, bytes]
FileTypes = Union[
    # file (or text)
    FileContent,
    # (filename, file (or text))
    Tuple[Optional[str], FileContent],
    # (filename, file (or text), content_type)
    Tuple[Optional[str], FileContent, Optional[str]],
]

class EmptyBody(BaseModel):
    status_code: int
    text: str


class BaseObjectResp(BaseModel):
    string_data: str

    @validator("string_data", pre=True)
    def check(cls, v: str) -> str:
        type_hints = get_type_hints(cls)
        string_data_values: Tuple[str] = type_hints["string_data"].__dict__['__args__']

        if v not in string_data_values:
            raise ValueError(f'invalid string_data for {cls}')

        return v


class AllOfRefObj(BaseModel):
    """
    All Of
    """

    # required ---

    # optional ---
    id: Optional[str] = None
    data: Optional[int] = None


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


class RewardsListItem(BaseModel):
    """
    None
    """

    # required ---
    pricePlanCode: str
    quantity: float

    # optional ---


class GetObjectWithInlineArrayResponse200(BaseModel):
    """
    None
    """

    # required ---

    # optional ---
    rewards: Optional[List[RewardsListItem]] = None


class GetObjectWithInlineArrayResponse200Item(BaseModel):
    """
    None
    """

    # required ---
    pricePlanCode: str
    quantity: float

    # optional ---


class AnimalObj(BaseModel):
    """
    None
    """
    __root__: Union[
        'Cat',
        'Dog',
    ]


class TierObj(BaseModel):
    """
    None
    """

    # required ---

    # optional ---
    code: Optional[str] = None
    name: Optional[str] = None
    priority: Optional[int] = None


class GetObjectNoRefSchemaResponse200(BaseModel):
    """
    GetObjectResp
    """

    # required ---

    # optional ---
    string_data: Optional[str] = Field(description="String Data. [__discriminator__(BaseObjectResp.string_data)]")
    integer_data: Optional[int] = None
    array_data: Optional[List[str]] = None
    boolean_data: Optional[bool] = None


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
    array_data: List[str]
    boolean_data: bool
    event_data: Dict = Field(description="__safety_key__(event_data)", alias="event-data")

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


class Dog(BaseModel):
    """
    Dog
    """

    # required ---

    # optional ---
    name: Optional[str] = None


class Cat(BaseModel):
    """
    Cat
    """

    # required ---

    # optional ---
    name: Optional[str] = None


class GetObjectResp(BaseModel):
    """
    GetObjectResp
    """

    # required ---

    # optional ---
    string_data: Optional[str] = Field(description="String Data. [__discriminator__(BaseObjectResp.string_data)]")
    integer_data: Optional[int] = None
    array_data: Optional[List[str]] = None
    boolean_data: Optional[bool] = None
    tier: Optional[TierObj] = None
    animal: Optional[AnimalObj] = None


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
        client_name: str = "",
        client: Optional[httpx.Client] = None,
        headers: Optional[Dict[str, str]] = None,
        tracer_integration: Optional[BaseTracerIntegration] = None,
        metrics_integration: Optional[BaseMetricsIntegration] = None,
    ):
        self.client = client or httpx.Client(timeout=Timeout(timeout))
        self.base_url = base_url
        self.headers = headers or {}
        self.tracer_integration = tracer_integration
        self.metrics_integration=metrics_integration
        self.client_name = client_name
    
    @tracing
    def get_object_no_ref_schema(
        self,
        object_id: str,
        from_: str,
        return_error: Optional[str] = None,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[GetObjectNoRefSchemaResponse200]:
        url = self._get_url(f'/objects/no-ref-schema/{object_id}')

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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/objects/no-ref-schema/:object_id")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/objects/no-ref-schema/:object_id")

        if response.status_code == 200:
            return GetObjectNoRefSchemaResponse200.parse_obj(response.json())
    
    @tracing
    def get_object(
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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/objects/:object_id")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/objects/:object_id")

        if response.status_code == 200:
            return GetObjectResp.parse_obj(response.json())

        if response.status_code == 500:
            method = "get"
            if response.content is None:
                content = None
            else:
                content = response.content[:500]

            self.log_error(self.client_name, method, url, params, content, headers_)

            return UnknownError.parse_obj(response.json())
    
    @tracing
    def get_object_with_inline_array(
        self,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[List[GetObjectWithInlineArrayResponse200Item]]:
        url = self._get_url(f'/object-with-array-response')

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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/object-with-array-response")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/object-with-array-response")

        if response.status_code == 200:
            return [GetObjectWithInlineArrayResponse200Item.parse_obj(item) for item in response.json()]
    
    @tracing
    def get_object_with_inline_array(
        self,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[GetObjectWithInlineArrayResponse200]:
        url = self._get_url(f'/object-with-inline-array')

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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/object-with-inline-array")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/object-with-inline-array")

        if response.status_code == 200:
            return GetObjectWithInlineArrayResponse200.parse_obj(response.json())
    
    @tracing
    def get_list_objects(
        self,
        auth: Optional[BasicAuth] = None,
    ) -> Optional[List[GetObjectResp]]:
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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/objects")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/objects")

        if response.status_code == 200:
            return [GetObjectResp.parse_obj(item) for item in response.json()]
    
    @tracing
    def get_text(
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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/text")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/text")

        if response.status_code == 200:
            return GetTextResponse200(text=response.text)
    
    @tracing
    def get_empty(
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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/empty")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/empty")

        if response.status_code == 200:
            return EmptyBody(status_code=response.status_code, text=response.text)
    
    @tracing
    def get_binary(
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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/binary")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/binary")

        if response.status_code == 200:
            return GetBinaryResponse200(content=response.content)
    
    @tracing
    def get_allof(
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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/allof")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/allof")

        if response.status_code == 200:
            return AllOfResp.parse_obj(response.json())
    
    @tracing
    def get_object_slow(
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
            response = self.client.get(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "get", "/slow/objects/:object_id")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "get", "/slow/objects/:object_id")

        if response.status_code == 200:
            return GetObjectResp.parse_obj(response.json())

        if response.status_code == 500:
            method = "get"
            if response.content is None:
                content = None
            else:
                content = response.content[:500]

            self.log_error(self.client_name, method, url, params, content, headers_)

            return UnknownError.parse_obj(response.json())
    
    @tracing
    def post_object_without_body(
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
            response = self.client.post(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "post", "/post-without-body")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "post", "/post-without-body")

        if response.status_code == 200:
            return PostObjectResp.parse_obj(response.json())
    
    @tracing
    def post_object(
        self,
        body: Optional[Union[PostObjectData, Dict[str, Any]]] = None,
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
            response = self.client.post(url, json=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "post", "/objects")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "post", "/objects")

        if response.status_code == 200:
            return PostObjectResp.parse_obj(response.json())
    
    @tracing
    def post_form_object(
        self,
        body: Optional[Union[PostObjectData, Dict[str, Any]]] = None,
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
            response = self.client.post(url, data=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "post", "/objects-form-data")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "post", "/objects-form-data")

        if response.status_code == 200:
            return PostObjectResp.parse_obj(response.json())
    
    @tracing
    def post_multipart_form_data(
        self,
        body: Optional[Union[PostFile, Dict[str, Any]]] = None,
        auth: Optional[BasicAuth] = None,
        files: Optional[Union[Mapping[str, FileTypes], Sequence[Tuple[str, FileTypes]]]] = None,
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
            response = self.client.post(url, data=json, headers=headers_, params=params, auth=auth_, files=files)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "post", "/multipart-form-data")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "post", "/multipart-form-data")

        if response.status_code == 200:
            return PostObjectResp.parse_obj(response.json())
    
    @tracing
    def patch_object(
        self,
        object_id: str,
        body: Optional[Union[PatchObjectData, Dict[str, Any]]] = None,
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
            response = self.client.patch(url, json=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "patch", "/objects/:object_id")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "patch", "/objects/:object_id")

        if response.status_code == 200:
            return PatchObjectResp.parse_obj(response.json())
    
    @tracing
    def put_object(
        self,
        object_id: str,
        body: Optional[Union[PutObjectData, Dict[str, Any]]] = None,
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
            response = self.client.put(url, json=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "put", "/objects/:object_id")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "put", "/objects/:object_id")

        if response.status_code == 200:
            return PutObjectResp.parse_obj(response.json())
    
    @tracing
    def put_object_slow(
        self,
        object_id: str,
        body: Optional[Union[PutObjectData, Dict[str, Any]]] = None,
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
            response = self.client.put(url, json=json, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "put", "/slow/objects/:object_id")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "put", "/slow/objects/:object_id")

        if response.status_code == 200:
            return PutObjectResp.parse_obj(response.json())
    
    @tracing
    def delete_object(
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
            response = self.client.delete(url, headers=headers_, params=params, auth=auth_)
        except Exception as exc:
            if self.metrics_integration:
                self.metrics_integration.on_request_error(self.client_name, exc, "delete", "/objects/:object_id")
            raise exc
        
        if self.metrics_integration:
            self.metrics_integration.on_request_success(self.client_name, response, "delete", "/objects/:object_id")

        if response.status_code == 200:
            return DeleteObjectResp.parse_obj(response.json())
    
    
    def close(self) -> None:
        self.client.close()

    def _get_url(self, path: str) -> str:
        return f'{self.base_url}{path}'

    def log_extra(self, **kwargs: Any) -> Dict[str, Any]:
        return {'extra': {'props': {'data': kwargs}}}

    def log_error(self, client_name: str, method, url: str, params, content, headers) -> None:
        msg = f"request error"
        msg += f" | client={client_name}"
        msg += f" | method={method}"
        msg += f" | url={url}"
        msg += f" | params={params}"
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

    def add_tracing_data_to_headers(self, headers_: Dict[str, str]) -> None:
        tracing_headers = self.tracer_integration.get_tracing_http_headers()
        headers_.update(tracing_headers)
        trace_id = self.tracer_integration.get_current_trace_id() or ''
        headers_['x-trace-id'] = trace_id


AllOfRefObj.update_forward_refs()
GetBinaryResponse200.update_forward_refs()
GetTextResponse200.update_forward_refs()
GetListobjectsResponse200.update_forward_refs()
RewardsListItem.update_forward_refs()
GetObjectWithInlineArrayResponse200.update_forward_refs()
GetObjectWithInlineArrayResponse200Item.update_forward_refs()
AnimalObj.update_forward_refs()
TierObj.update_forward_refs()
GetObjectNoRefSchemaResponse200.update_forward_refs()
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
Dog.update_forward_refs()
Cat.update_forward_refs()
GetObjectResp.update_forward_refs()
Data.update_forward_refs()
AllOfResp.update_forward_refs()
