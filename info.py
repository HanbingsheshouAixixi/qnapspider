# utils.py

import socket
import bisect
from enum import Enum

# 记录类型的常量
httpsSmartLanIPv4 = 0
httpsSmartLanIPv6 = 1
httpsLanIPv4 = 2
httpsLanIPv6 = 3
httpsFQDN = 4
httpsDDNS = 5
httpsSmartHost = 6
httpsSmartWanIPv6 = 7
httpsSmartWanIPv4 = 8
httpsWanIPv6 = 9
httpsWanIPv4 = 10
httpLanIPv4 = 11
httpLanIPv6 = 12
httpFQDN = 13
httpDDNS = 14
httpWanIPv6 = 15
httpWanIPv4 = 16
httpsTun = 17
httpTun = 18
maxRecordType = 19


def is_https(t):
    # 判断是否为 HTTPS 类型
    return t < httpLanIPv4 or t == httpsTun


# ConnState 表示与 URL/主机的连接状态
class ConnState(Enum):
    StateUnknown = 0
    StateOK = 1
    StateConnectFailed = 2
    StateInvalidServer = 3


# Record 是一个单个 QuickConnect 重定向记录，指示可能能够访问所需 Synology 服务的 URL。
# 每个记录有一个 Type 用于优先级排序，以及一个 State 表示最近一次连接测试的结果。
class Record:
    def __init__(self, URL, Type, State=ConnState.StateUnknown):
        self.URL = URL
        self.Type = Type
        self.State = State


# Info 包含有关 QuickConnect 主机的信息
class Info:
    def __init__(self, ServerID="", Records=None):
        self.ServerID = ServerID
        self.Records = Records if Records is not None else []

    # 将 Record 添加到 Info 中，并按 Record.Type 排序
    def add(self, r):
        s = self.Records

        # 找到插入点
        i = bisect.bisect_left(s, r, key=lambda x: x.Type)

        if i == len(s):
            # 将记录追加到当前集合的末尾
            s.append(r)
        else:
            # 在索引 i 处插入
            s.insert(i, r)

        self.Records = s


# 参考自 / 复制自 https://go-review.googlesource.com/c/go/+/162998/7/src/net/ip.go
def is_local_ip(addr):
    try:
        ip = socket.inet_pton(socket.AF_INET, addr)
        first_byte = ip[0]
        return first_byte == 10 or \
            (first_byte == 172 and (ip[1] & 0xf0) == 16) or \
            (first_byte == 192 and ip[1] == 168)
    except socket.error:
        try:
            ip = socket.inet_pton(socket.AF_INET6, addr)
            return (ip[0] & 0xfe) == 0xfc
        except socket.error:
            return False
