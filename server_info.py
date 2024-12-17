# server_info.py
import json
import requests
from io import BytesIO
from typing import List, Dict, Any
from enum import Enum

DEFAULT_TIMEOUT = 2


# 自定义错误
class ErrUnknownCommand(Exception):
    pass


class ErrUnknownServerType(Exception):
    pass


class ErrParse(Exception):
    pass


# JSON response
class env:
    def __init__(self, control_host: str, relay_region: str):
        self.control_host = control_host
        self.relay_region = relay_region


class smartdns:
    def __init__(self, host: str, external: str, externalv6: str, lan: List[str], lanv6: List[str], hole_punch: str):
        self.host = host
        self.external = external
        self.externalv6 = externalv6
        self.lan = lan
        self.lanv6 = lanv6
        self.hole_punch = hole_punch


class serverInfo:
    def __init__(self, Command: str, Env: env, ErrNo: int, Service: 'service', Server: 'server', Smartdns: 'smartdns'):
        self.Command = Command
        self.Env = Env
        self.ErrNo = ErrNo
        self.Service = Service
        self.Server = Server
        self.Smartdns = Smartdns


class service:
    def __init__(self, Port: int, ExtPort: int, RelayIP: str, RelayIPv6: str, RelayPort: int, HttpsIP: str,
                 HttpsPort: int, PingpongDesc: list[str]):
        self.Port = Port
        self.ExtPort = ExtPort
        self.RelayIP = RelayIP
        self.RelayIPv6 = RelayIPv6
        self.RelayPort = RelayPort
        self.HttpsIP = HttpsIP
        self.HttpsPort = HttpsPort
        self.PingpongDesc = PingpongDesc


class server:
    def __init__(self, DDNS: str, FQDN: str, External: 'extIPs', Interface: List['iface'], ServerID: str):
        self.DDNS = DDNS
        self.FQDN = FQDN
        self.External = External
        self.Interface = Interface
        self.ServerID = ServerID


class extIPs:
    def __init__(self, IP: str, IPv6: str):
        self.IP = IP
        self.IPv6 = IPv6


class iface:
    def __init__(self, IP: str, IPv6: List['ipv6']):
        self.IP = IP
        self.IPv6 = IPv6


class ipv6:
    def __init__(self, Address: str, Scope: str):
        self.Address = Address
        self.Scope = Scope


# commands are either 'get_server_info' or 'request_tunnel'
# ids are 'dsm_portal_https', 'dsm_portal', 'photo_portal_https' or 'photo_portal_http'
SERVER_QUERY = '''[
  {{
    "version": 1,
    "command": "{}",
    "stop_when_error": false,
    "stop_when_success": false,
    "id": "{}",
    "serverID": "{}",
    "is_gofile": false
  }},
  {{
    "version": 1,
    "command": "{}",
    "stop_when_error": false,
    "stop_when_success": false,
    "id": "{}",
    "serverID": "{}",
    "is_gofile": false
  }}
]'''


def new_request_body(cmd: str, typ: str, serverID: str) -> BytesIO:
    if cmd not in ["get_server_info", "request_tunnel"]:
        raise ErrUnknownCommand

    # if typ not in ["dsm", "photo"]:
    #     raise ErrUnknownServerType

    query = SERVER_QUERY.format(cmd, f"{typ}_https", serverID, cmd, f"{typ}_http", serverID)
    return BytesIO(query.encode())


def get_server_info(ctx, c: requests.Session, serv_url: str, id: str) -> List[serverInfo]:
    req_body = new_request_body("get_server_info", "mainapp", id)

    with c.post(serv_url, data=req_body.read(), timeout=DEFAULT_TIMEOUT) as resp:
        resp.raise_for_status()

        info_list = resp.json()
        print(info_list)
        if len(info_list) != 2:
            raise ErrParse

        info = []
        errno_not_zero = False

        for item in info_list:
            if item["errno"] != 0:
                print(f"get_server_info returned errno={item['errno']}")
                info.append(serverInfo(Command=item["command"], ErrNo=item["errno"],
                                       Env=env("", ""),
                                       Service=service(0, 0, "", "", 0, "", 0, []),
                                       Server=server("", "", extIPs("", ""), [], ""),
                                       Smartdns=smartdns("", "", "", [], [], "")))
                continue
            else:
                errno_not_zero = True

            service_data = item["service"]
            server_data = item["server"]
            smartdns_data = item["smartdns"]
            env_data = item["env"]

            env_obj = env(control_host=env_data.get("control_host", ""),
                          relay_region=env_data.get("relay_region", ""))

            service_obj = service(
                Port=service_data.get("port", ""),
                ExtPort=service_data.get("ext_port", ""),
                RelayIP=service_data.get("relay_ip", ""),
                RelayIPv6=service_data.get("relay_ipv6", ""),
                RelayPort=service_data.get("relay_port", ""),
                HttpsIP=service_data.get("https_ip", ""),
                HttpsPort=service_data.get("https_port", ""),
                PingpongDesc=service_data.get("pingpong_desc", [])
            )

            external_data = server_data["external"]
            external_obj = extIPs(
                IP=external_data["ip"],
                IPv6=external_data["ipv6"]
            )

            interface_list = []
            for iface_data in server_data["interface"]:
                ipv6_list = [ipv6(Address=ip["address"], Scope=ip["scope"]) for ip in iface_data["ipv6"]]
                interface_list.append(iface(IP=iface_data["ip"], IPv6=ipv6_list))

            server_obj = server(
                DDNS=server_data.get("ddns", ""),
                FQDN=server_data.get("fqdn", ""),
                External=external_obj,
                Interface=interface_list,
                ServerID=server_data.get("serverID", "")
            )

            smartdns_obj = smartdns(
                host=smartdns_data.get("host", ""),
                external=smartdns_data.get("external", ""),
                externalv6=smartdns_data.get("externalv6", ""),
                lan=smartdns_data.get("lan", []),
                lanv6=smartdns_data.get("lanv6", []),
                hole_punch=smartdns_data.get("hole_punch", "")
            )

            info.append(
                serverInfo(Command=item["command"], Env=env_obj, ErrNo=item["errno"], Service=service_obj,
                           Server=server_obj,
                           Smartdns=smartdns_obj))

        if not errno_not_zero:
            raise ErrParse
        return info
