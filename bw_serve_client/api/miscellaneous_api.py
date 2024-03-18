# coding: utf-8

"""
    Vault Management API

    This schema documents the endpoints available to the Vault Management API, accessible from the Bitwarden CLI using the `bw serve` command ([learn more](https://bitwarden.com/help/cli/)). If you're looking for the **Organization Management** API, refer instead to [this document](https://bitwarden.com/help/api/).

    The version of the OpenAPI document: latest
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501

import re  # noqa: F401
import io
import warnings

from pydantic import validate_arguments, ValidationError

from typing_extensions import Annotated
from pydantic import Field, StrictBool, StrictInt, StrictStr

from typing import Optional

from bw_serve_client.models.status import Status

from bw_serve_client.api_client import ApiClient
from bw_serve_client.api_response import ApiResponse
from bw_serve_client.exceptions import (  # noqa: F401
    ApiTypeError, ApiValueError)


class MiscellaneousApi:
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None) -> None:
        if api_client is None:
            api_client = ApiClient.get_default()
        self.api_client = api_client

    @validate_arguments
    def generate_get(
            self,
            length: Annotated[
                Optional[StrictInt],
                Field(description="Number of characters in the **password**."
                      )] = None,
            uppercase: Annotated[
                Optional[StrictBool],
                Field(description=
                      "Include uppercase characters in the **password**."
                      )] = None,
            lowercase: Annotated[
                Optional[StrictBool],
                Field(description=
                      "Include lowercase characters in the **password**."
                      )] = None,
            number: Annotated[
                Optional[StrictBool],
                Field(description="Include numbers in the **password**."
                      )] = None,
            special: Annotated[
                Optional[StrictBool],
                Field(
                    description=
                    "Include special characters in the **password**.")] = None,
            passphrase:
        Annotated[
            Optional[StrictBool],
            Field(
                description=
                "Generate passphrase (by default, `/generate` will generate a password)."
            )] = None,
            words: Annotated[
                Optional[StrictInt],
                Field(description="Number of words in the **passphrase**."
                      )] = None,
            separator: Annotated[
                Optional[StrictStr],
                Field(description="Separator character in the **passphrase**."
                      )] = None,
            capitalize: Annotated[
                Optional[StrictBool],
                Field(description="Title-case the **passphrase**.")] = None,
            include_number: Annotated[
                Optional[StrictBool],
                Field(description="Include numbers in the **passphrase**."
                      )] = None,
            **kwargs) -> None:  # noqa: E501
        """Generate a password or passphrase.  # noqa: E501

        Generate a password or passphrase. By default, `/generate` will generate a 14-character password with uppercase characters, lowercase characters, and numbers.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.generate_get(length, uppercase, lowercase, number, special, passphrase, words, separator, capitalize, include_number, async_req=True)
        >>> result = thread.get()

        :param length: Number of characters in the **password**.
        :type length: int
        :param uppercase: Include uppercase characters in the **password**.
        :type uppercase: bool
        :param lowercase: Include lowercase characters in the **password**.
        :type lowercase: bool
        :param number: Include numbers in the **password**.
        :type number: bool
        :param special: Include special characters in the **password**.
        :type special: bool
        :param passphrase: Generate passphrase (by default, `/generate` will generate a password).
        :type passphrase: bool
        :param words: Number of words in the **passphrase**.
        :type words: int
        :param separator: Separator character in the **passphrase**.
        :type separator: str
        :param capitalize: Title-case the **passphrase**.
        :type capitalize: bool
        :param include_number: Include numbers in the **passphrase**.
        :type include_number: bool
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request.
               If one number provided, it will be total request
               timeout. It can also be a pair (tuple) of
               (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            message = "Error! Please call the generate_get_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data"  # noqa: E501
            raise ValueError(message)
        return self.generate_get_with_http_info(length, uppercase, lowercase,
                                                number, special, passphrase,
                                                words, separator, capitalize,
                                                include_number,
                                                **kwargs)  # noqa: E501

    @validate_arguments
    def generate_get_with_http_info(
            self,
            length: Annotated[
                Optional[StrictInt],
                Field(description="Number of characters in the **password**."
                      )] = None,
            uppercase: Annotated[
                Optional[StrictBool],
                Field(description=
                      "Include uppercase characters in the **password**."
                      )] = None,
            lowercase: Annotated[
                Optional[StrictBool],
                Field(description=
                      "Include lowercase characters in the **password**."
                      )] = None,
            number: Annotated[
                Optional[StrictBool],
                Field(description="Include numbers in the **password**."
                      )] = None,
            special: Annotated[
                Optional[StrictBool],
                Field(
                    description=
                    "Include special characters in the **password**.")] = None,
            passphrase:
        Annotated[
            Optional[StrictBool],
            Field(
                description=
                "Generate passphrase (by default, `/generate` will generate a password)."
            )] = None,
            words: Annotated[
                Optional[StrictInt],
                Field(description="Number of words in the **passphrase**."
                      )] = None,
            separator: Annotated[
                Optional[StrictStr],
                Field(description="Separator character in the **passphrase**."
                      )] = None,
            capitalize: Annotated[
                Optional[StrictBool],
                Field(description="Title-case the **passphrase**.")] = None,
            include_number: Annotated[
                Optional[StrictBool],
                Field(description="Include numbers in the **passphrase**."
                      )] = None,
            **kwargs) -> ApiResponse:  # noqa: E501
        """Generate a password or passphrase.  # noqa: E501

        Generate a password or passphrase. By default, `/generate` will generate a 14-character password with uppercase characters, lowercase characters, and numbers.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.generate_get_with_http_info(length, uppercase, lowercase, number, special, passphrase, words, separator, capitalize, include_number, async_req=True)
        >>> result = thread.get()

        :param length: Number of characters in the **password**.
        :type length: int
        :param uppercase: Include uppercase characters in the **password**.
        :type uppercase: bool
        :param lowercase: Include lowercase characters in the **password**.
        :type lowercase: bool
        :param number: Include numbers in the **password**.
        :type number: bool
        :param special: Include special characters in the **password**.
        :type special: bool
        :param passphrase: Generate passphrase (by default, `/generate` will generate a password).
        :type passphrase: bool
        :param words: Number of words in the **passphrase**.
        :type words: int
        :param separator: Separator character in the **passphrase**.
        :type separator: str
        :param capitalize: Title-case the **passphrase**.
        :type capitalize: bool
        :param include_number: Include numbers in the **passphrase**.
        :type include_number: bool
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        _params = locals()

        _all_params = [
            'length', 'uppercase', 'lowercase', 'number', 'special',
            'passphrase', 'words', 'separator', 'capitalize', 'include_number'
        ]
        _all_params.extend([
            'async_req', '_return_http_data_only', '_preload_content',
            '_request_timeout', '_request_auth', '_content_type', '_headers'
        ])

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError("Got an unexpected keyword argument '%s'"
                                   " to method generate_get" % _key)
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

        # process the query parameters
        _query_params = []
        if _params.get('length') is not None:  # noqa: E501
            _query_params.append(('length', _params['length']))

        if _params.get('uppercase') is not None:  # noqa: E501
            _query_params.append(('uppercase', _params['uppercase']))

        if _params.get('lowercase') is not None:  # noqa: E501
            _query_params.append(('lowercase', _params['lowercase']))

        if _params.get('number') is not None:  # noqa: E501
            _query_params.append(('number', _params['number']))

        if _params.get('special') is not None:  # noqa: E501
            _query_params.append(('special', _params['special']))

        if _params.get('passphrase') is not None:  # noqa: E501
            _query_params.append(('passphrase', _params['passphrase']))

        if _params.get('words') is not None:  # noqa: E501
            _query_params.append(('words', _params['words']))

        if _params.get('separator') is not None:  # noqa: E501
            _query_params.append(('separator', _params['separator']))

        if _params.get('capitalize') is not None:  # noqa: E501
            _query_params.append(('capitalize', _params['capitalize']))

        if _params.get('include_number') is not None:  # noqa: E501
            _query_params.append(('includeNumber', _params['include_number']))

        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # authentication setting
        _auth_settings = []  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            '/generate',
            'GET',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get(
                '_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))

    @validate_arguments
    def object_fingerprint_me_get(self, **kwargs) -> None:  # noqa: E501
        """Retrieve your fingerprint phrase.  # noqa: E501

        Retrieve your fingerprint phrase.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.object_fingerprint_me_get(async_req=True)
        >>> result = thread.get()

        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request.
               If one number provided, it will be total request
               timeout. It can also be a pair (tuple) of
               (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            message = "Error! Please call the object_fingerprint_me_get_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data"  # noqa: E501
            raise ValueError(message)
        return self.object_fingerprint_me_get_with_http_info(
            **kwargs)  # noqa: E501

    @validate_arguments
    def object_fingerprint_me_get_with_http_info(
            self, **kwargs) -> ApiResponse:  # noqa: E501
        """Retrieve your fingerprint phrase.  # noqa: E501

        Retrieve your fingerprint phrase.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.object_fingerprint_me_get_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        _params = locals()

        _all_params = []
        _all_params.extend([
            'async_req', '_return_http_data_only', '_preload_content',
            '_request_timeout', '_request_auth', '_content_type', '_headers'
        ])

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError("Got an unexpected keyword argument '%s'"
                                   " to method object_fingerprint_me_get" %
                                   _key)
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

        # process the query parameters
        _query_params = []
        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # authentication setting
        _auth_settings = []  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            '/object/fingerprint/me',
            'GET',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get(
                '_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))

    @validate_arguments
    def object_template_type_get(self, type: StrictStr,
                                 **kwargs) -> None:  # noqa: E501
        """Retrieve a JSON template for any object.  # noqa: E501

        Retreive a JSON template for any object, including vault items, sends, folders, and more. Templates can be used to guide you in creation of new objects.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.object_template_type_get(type, async_req=True)
        >>> result = thread.get()

        :param type: (required)
        :type type: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request.
               If one number provided, it will be total request
               timeout. It can also be a pair (tuple) of
               (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            message = "Error! Please call the object_template_type_get_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data"  # noqa: E501
            raise ValueError(message)
        return self.object_template_type_get_with_http_info(
            type, **kwargs)  # noqa: E501

    @validate_arguments
    def object_template_type_get_with_http_info(
            self, type: StrictStr, **kwargs) -> ApiResponse:  # noqa: E501
        """Retrieve a JSON template for any object.  # noqa: E501

        Retreive a JSON template for any object, including vault items, sends, folders, and more. Templates can be used to guide you in creation of new objects.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.object_template_type_get_with_http_info(type, async_req=True)
        >>> result = thread.get()

        :param type: (required)
        :type type: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        _params = locals()

        _all_params = ['type']
        _all_params.extend([
            'async_req', '_return_http_data_only', '_preload_content',
            '_request_timeout', '_request_auth', '_content_type', '_headers'
        ])

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError("Got an unexpected keyword argument '%s'"
                                   " to method object_template_type_get" %
                                   _key)
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}
        if _params['type'] is not None:
            _path_params['type'] = _params['type']

        # process the query parameters
        _query_params = []
        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # authentication setting
        _auth_settings = []  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            '/object/template/{type}',
            'GET',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get(
                '_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))

    @validate_arguments
    def status_get(self, **kwargs) -> Status:  # noqa: E501
        """Get the status of the Bitwarden CLI.  # noqa: E501

        Get the current `serverURL`, `lastSync`, `userEmail`, `userID`, and `status` of your Bitwarden CLI client.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.status_get(async_req=True)
        >>> result = thread.get()

        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request.
               If one number provided, it will be total request
               timeout. It can also be a pair (tuple) of
               (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: Status
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            message = "Error! Please call the status_get_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data"  # noqa: E501
            raise ValueError(message)
        return self.status_get_with_http_info(**kwargs)  # noqa: E501

    @validate_arguments
    def status_get_with_http_info(self, **kwargs) -> ApiResponse:  # noqa: E501
        """Get the status of the Bitwarden CLI.  # noqa: E501

        Get the current `serverURL`, `lastSync`, `userEmail`, `userID`, and `status` of your Bitwarden CLI client.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.status_get_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(Status, status_code(int), headers(HTTPHeaderDict))
        """

        _params = locals()

        _all_params = []
        _all_params.extend([
            'async_req', '_return_http_data_only', '_preload_content',
            '_request_timeout', '_request_auth', '_content_type', '_headers'
        ])

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError("Got an unexpected keyword argument '%s'"
                                   " to method status_get" % _key)
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

        # process the query parameters
        _query_params = []
        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # authentication setting
        _auth_settings = []  # noqa: E501

        _response_types_map = {
            '200': "Status",
            '400': None,
            '404': None,
            '500': None,
        }

        return self.api_client.call_api(
            '/status',
            'GET',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get(
                '_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))

    @validate_arguments
    def sync_post(self, **kwargs) -> None:  # noqa: E501
        """Sync your vault.  # noqa: E501

        Sync your vault.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.sync_post(async_req=True)
        >>> result = thread.get()

        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _request_timeout: timeout setting for this request.
               If one number provided, it will be total request
               timeout. It can also be a pair (tuple) of
               (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs['_return_http_data_only'] = True
        if '_preload_content' in kwargs:
            message = "Error! Please call the sync_post_with_http_info method with `_preload_content` instead and obtain raw data from ApiResponse.raw_data"  # noqa: E501
            raise ValueError(message)
        return self.sync_post_with_http_info(**kwargs)  # noqa: E501

    @validate_arguments
    def sync_post_with_http_info(self, **kwargs) -> ApiResponse:  # noqa: E501
        """Sync your vault.  # noqa: E501

        Sync your vault.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.sync_post_with_http_info(async_req=True)
        >>> result = thread.get()

        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the ApiResponse.data will
                                 be set to none and raw_data will store the
                                 HTTP response body without reading/decoding.
                                 Default is True.
        :type _preload_content: bool, optional
        :param _return_http_data_only: response data instead of ApiResponse
                                       object with status code, headers, etc
        :type _return_http_data_only: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        _params = locals()

        _all_params = []
        _all_params.extend([
            'async_req', '_return_http_data_only', '_preload_content',
            '_request_timeout', '_request_auth', '_content_type', '_headers'
        ])

        # validate the arguments
        for _key, _val in _params['kwargs'].items():
            if _key not in _all_params:
                raise ApiTypeError("Got an unexpected keyword argument '%s'"
                                   " to method sync_post" % _key)
            _params[_key] = _val
        del _params['kwargs']

        _collection_formats = {}

        # process the path parameters
        _path_params = {}

        # process the query parameters
        _query_params = []
        # process the header parameters
        _header_params = dict(_params.get('_headers', {}))
        # process the form parameters
        _form_params = []
        _files = {}
        # process the body parameter
        _body_params = None
        # set the HTTP header `Accept`
        _header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # authentication setting
        _auth_settings = []  # noqa: E501

        _response_types_map = {}

        return self.api_client.call_api(
            '/sync',
            'POST',
            _path_params,
            _query_params,
            _header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            response_types_map=_response_types_map,
            auth_settings=_auth_settings,
            async_req=_params.get('async_req'),
            _return_http_data_only=_params.get(
                '_return_http_data_only'),  # noqa: E501
            _preload_content=_params.get('_preload_content', True),
            _request_timeout=_params.get('_request_timeout'),
            collection_formats=_collection_formats,
            _request_auth=_params.get('_request_auth'))
