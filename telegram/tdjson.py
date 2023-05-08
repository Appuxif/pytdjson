import json
import logging
from ctypes import CDLL, CFUNCTYPE, c_char_p, c_double, c_int, c_void_p
from typing import Any, Dict, Optional, Union

import pkg_resources

logger = logging.getLogger(__name__)


def _get_tdjson_lib_path() -> str:
    lib_name = 'linux/libtdjson.so'

    return pkg_resources.resource_filename('telegram', f'lib/{lib_name}')


class TDJson:
    def __init__(self, library_path: Optional[str] = None, verbosity: int = 2) -> None:
        if library_path is None:
            library_path = _get_tdjson_lib_path()

        self._build_client(library_path, verbosity)

    def __del__(self) -> None:
        self.stop()

    def _build_client(self, library_path: str, verbosity: int) -> None:
        self._tdjson = CDLL(library_path)

        # load TDLib functions from shared library
        self._td_create_client_id = self._tdjson.td_create_client_id
        self._td_create_client_id.restype = c_int
        self._td_create_client_id.argtypes = []

        self.td_client_id = self._td_create_client_id()

        self._td_receive = self._tdjson.td_receive
        self._td_receive.restype = c_char_p
        self._td_receive.argtypes = [c_double]

        self._td_send = self._tdjson.td_send
        self._td_send.restype = None
        self._td_send.argtypes = [c_int, c_char_p]

        self._td_execute = self._tdjson.td_execute
        self._td_execute.restype = c_char_p
        self._td_execute.argtypes = [c_char_p]

        self._td_json_client_destroy = self._tdjson.td_json_client_destroy
        self._td_json_client_destroy.restype = None
        self._td_json_client_destroy.argtypes = [c_void_p]

        # Segmentation fault (core dumped)
        # log_message_callback_type = CFUNCTYPE(None, c_int, c_char_p)
        # self._td_set_log_message_callback = self._tdjson.td_set_log_message_callback
        # self._td_set_log_message_callback.restype = None
        # self._td_set_log_message_callback.argtypes = [c_int, log_message_callback_type]
        #
        # # initialize TDLib log with desired parameters
        # @log_message_callback_type
        # def on_log_message_callback(verbosity_level, message):
        #     logger.debug('%s: %s', verbosity_level, message)
        #     if verbosity_level == 0:
        #         logger.error('TDLib fatal error: %s', message)
        #
        # self._td_set_log_message_callback(2, on_log_message_callback)
        self.td_execute(
            {'@type': 'setLogVerbosityLevel', 'new_verbosity_level': verbosity}
        )

        # another test for TDLib execute method
        logger.debug(
            self.td_execute(
                {
                    '@type': 'getTextEntities',
                    'text': '@telegram /test_command https://telegram.org telegram.me',
                    '@extra': ['5', 7.0, 'a'],
                }
            )
        )

        # start the client by sending a request to it
        self.send({'@type': 'getOption', 'name': 'version'})

    def send(self, query: Dict[Any, Any]) -> None:
        dumped_query = json.dumps(query).encode('utf-8')
        self._td_send(self.td_client_id, dumped_query)

    def receive(self) -> Union[None, Dict[Any, Any]]:
        result_str = self._td_receive(1.0)

        if result_str:
            result: Dict[Any, Any] = json.loads(result_str.decode('utf-8'))
            return result

        return None

    def td_execute(self, query: Dict[Any, Any]) -> Union[Dict[Any, Any], Any]:
        dumped_query = json.dumps(query).encode('utf-8')
        result_str = self._td_execute(dumped_query)

        if result_str:
            result: Dict[Any, Any] = json.loads(result_str.decode('utf-8'))
            return result

        return None

    def stop(self) -> None:
        if hasattr(self, '_tdjson') and hasattr(
            self._tdjson, '_td_json_client_destroy'
        ):
            self._td_json_client_destroy(self.td_client_id)
