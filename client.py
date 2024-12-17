import contextlib
import threading
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from enum import Enum
from info import Info, Record

from server_info import serverInfo, get_server_info
from info import maxRecordType, is_https as is_https_info, is_local_ip as is_local_ip_info

# 导入自定义错误
from errors import ErrTimeout, ErrCannotAccess, PingFailureError

# 默认客户端设置
DEFAULT_TIMEOUT = 10
DEFAULT_SERV_URL_DEC = "https://dec.quickconnect.to/Serv.php"
DEFAULT_SERV_URL_GLOBAL = "https://global.quickconnect.to/Serv.php"


class State(Enum):
    OK = 1
    ConnectFailed = 2
    InvalidServer = 3


class Client:
    def __init__(self, client=None, timeout=0, serv_url=""):
        self.client = client
        self.timeout = timeout
        self.serv_url = serv_url if serv_url else DEFAULT_SERV_URL_DEC

    def get_info(self, ctx, id: str):
        rs = Info()

        if not ctx:
            ctx = contextlib.nullcontext()

        with ctx:

            http_client = self.client if self.client else requests.Session()

            serv_url = self.serv_url if self.serv_url else DEFAULT_SERV_URL_DEC

            # 获取服务器上的信息
            try:
                info = get_server_info(ctx, http_client, serv_url, id)
            except Exception as e:
                info = get_server_info(ctx, http_client, DEFAULT_SERV_URL_GLOBAL, id)

            if isinstance(info, Exception):
                return rs, info

            rs.ServerID = info[0].Server.ServerID

            rs.Records = []

            # for t in range(max_record_type):
            #     if is_https(t):
            #         i = info[0]
            #     else:
            #         if info[1].ErrNo != 0:
            #             continue  # 如果 ErrNo 不等于 0，跳过本次循环
            #         i = info[1]
            #
            #     for u in get_urls(i, t):
            #         rs.Records.append(Record(URL=u, Type=t))
            for i in (0, 1):
                server_info = info[i]
                if server_info.ErrNo != 0:
                    continue
                if i == 0:
                    url_type = 0
                    protocol = "https://"
                    if server_info.Service.HttpsIP is not None and server_info.Service.HttpsIP != "" and server_info.Service.HttpsPort is not None and server_info.Service.HttpsPort != 0:
                        rs.Records.append(
                            Record(
                                URL=f"{protocol}{id}.{server_info.Env.relay_region}.quickconnect.to:{server_info.Service.HttpsPort}",
                                Type=url_type))
                else:
                    url_type = 13
                    protocol = "http://"
                    if server_info.Service.RelayIP is not None and server_info.Service.RelayIP != "" and server_info.Service.RelayPort is not None and server_info.Service.RelayPort != 0:
                        rs.Records.append(
                            Record(
                                URL=f"{protocol}{id}.{server_info.Env.relay_region}.quickconnect.to:{server_info.Service.RelayPort}",
                                Type=url_type))
                # 添加记录
                add_record_if_valid(rs, server_info.Server.DDNS, server_info.Service.Port, url_type, protocol)
                add_record_if_valid(rs, server_info.Server.DDNS, server_info.Service.ExtPort, url_type, protocol)

                add_record_if_valid(rs, server_info.Server.FQDN, server_info.Service.Port, url_type, protocol)
                add_record_if_valid(rs, server_info.Server.FQDN, server_info.Service.ExtPort, url_type, protocol)

                add_record_if_valid(rs, server_info.Smartdns.host, server_info.Service.Port, url_type, protocol)
                add_record_if_valid(rs, server_info.Smartdns.host, server_info.Service.ExtPort, url_type, protocol)

                add_record_if_valid(rs, server_info.Smartdns.externalv6, server_info.Service.Port, url_type, protocol)
                add_record_if_valid(rs, server_info.Smartdns.externalv6, server_info.Service.ExtPort, url_type,
                                    protocol)

                for host_pingpong_desc in server_info.Service.PingpongDesc:
                    add_record_if_valid(rs, host_pingpong_desc, server_info.Service.Port, url_type, protocol)
                    add_record_if_valid(rs, host_pingpong_desc, server_info.Service.ExtPort, url_type, protocol)
                for host_lan in server_info.Smartdns.lan:
                    add_record_if_valid(rs, host_lan, server_info.Service.Port, url_type, protocol)
                    add_record_if_valid(rs, host_lan, server_info.Service.ExtPort, url_type, protocol)
                for host_lanv6 in server_info.Smartdns.lanv6:
                    add_record_if_valid(rs, host_lanv6, server_info.Service.Port, url_type, protocol)
                    add_record_if_valid(rs, host_lanv6, server_info.Service.ExtPort, url_type, protocol)
            return rs, None

    def update_state(self, ctx, info: Info):
        error_info = {'value': None}
        timeout = threading.Timer(self.timeout if self.timeout > 0 else DEFAULT_TIMEOUT,
                                  lambda: error_info.update({'value': ErrTimeout}))

        if not ctx:
            ctx = contextlib.nullcontext()

        with ctx:
            http_client = self.client if self.client else requests.Session()

            timeout.start()

            def ping_url(r: Record):
                nonlocal err
                try:
                    hash_value, err_ping = self.ping(ctx, r.URL)
                    if err_ping:
                        r.State = State.ConnectFailed
                        return

                    if not verify_id(info.ServerID, hash_value):
                        r.State = State.InvalidServer
                        return

                    r.State = State.OK
                    return

                except Exception as e:
                    r.State = State.ConnectFailed
                    return

            futures = []
            with ThreadPoolExecutor(max_workers=10) as executor:  # 限制并发请求数量
                for r in info.Records:
                    futures.append(executor.submit(ping_url, r))

            for future in as_completed(futures):
                if future.exception():
                    err = future.exception()
                    break

            timeout.cancel()
            timeout.join()

            return None

    def ping(self, ctx, url: str):
        """
        尝试向给定的 URL 发送 ping-pong 请求，并返回响应中的 ServerID 的 MD5 哈希值以供验证。
        """
        ping_path = "/webman/pingpong.cgi?action=cors&quickconnect=true"
        full_url = url + ping_path

        try:
            if self.client is None:
                self.client = requests.Session()

            with self.client.get(full_url, timeout=self.timeout if self.timeout > 0 else DEFAULT_TIMEOUT) as resp:
                resp.raise_for_status()

                json_resp = resp.json()

                if not json_resp.get('success', False):
                    return "", PingFailureError
                print(f"Ping success: {url} \n")

                return json_resp.get('ezid', ""), None

        except Exception as e:
            print(f"Ping failed: {url} \n")
            return "", PingFailureError(f"Ping failed: {e}")

    def resolve(self, ctx, id: str):
        """
        返回一个 URL 字符串列表，用于访问具有提供的 QuickConnect ID 的服务器。
        URL 字符串按优先级排序，最优先的排在前面，并且只返回具有验证连接性的 URL。
        """
        info, err = self.get_info(ctx, id)
        if err:
            return [], err

        err = self.update_state(ctx, info)
        if err:
            return [], err

        urls = [r.URL for r in info.Records if r.State == State.OK]

        if not urls:
            return [], ErrCannotAccess

        return urls, None


def get_urls(s: serverInfo, typ: int):
    if is_https(typ):
        return [f"https://{s.Service.HttpsIP}:{s.Service.HttpsPort}"]
    else:
        return [f"http://{s.Service.RelayIP}:{s.Service.RelayPort}"]


def is_https(t: int):
    return is_https_info(t)


def verify_id(server_id: str, hash_value: str):
    """
    验证 ID 的 MD5 哈希值是否匹配。
    """
    h = hashlib.md5(server_id.encode()).hexdigest()
    return h == hash_value


def is_local_ip(ip: str):
    return is_local_ip_info(ip)


max_record_type = maxRecordType

# 默认客户端，用于 resolve
DefaultClient = Client()
added_urls = set()


def add_record_if_valid(rs, url, port, url_type, protocol):
    if url is not None and url != "" and url != 'NULL' and port is not None and port != 0:
        full_url = f"{protocol}{url}:{port}"
        if full_url not in added_urls:
            rs.Records.append(Record(URL=full_url, Type=url_type))
            added_urls.add(full_url)


if __name__ == '__main__':
    print(DefaultClient.resolve(None, "youngfilestore"))  # nzaragosa 同时发tunnel host是control_host，后面处理逻辑基本一致
