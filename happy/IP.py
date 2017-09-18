#!/usr/bin/env python

#
#    Copyright (c) 2015-2017 Nest Labs, Inc.
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#


##
#    @file
#       Provides general IP formatting tools.
#

import socket


class IP:
    def __init__(self):
        pass

    def getIPv6Subnet(self, addr):
        a = addr.split(":")

        if len(a) > 3:
            return int(float(a[3]))
        else:
            None

    def getIPv6IID(self, addr):
        a = addr.split(":")

        if len(a) == 8:
            return str(":".join(a[4:]))
        else:
            return None

    def paddingZeros(self, addr_mask):
        if not self.isIpv6(addr_mask):
            return addr_mask

        if "/" in addr_mask:
            addr, mask = addr_mask.split("/")
        else:
            addr = addr_mask
            mask = None

        if "::" in addr:
            c = addr.count(":")
            missing = 8 - c

            in_zeros = ["0000"] * missing
            in_zeros = ":".join(in_zeros)

            addr = addr.split("::")
            if addr[1] == '':
                addr = addr[0] + ":" + in_zeros + ":0000"
            else:
                addr = addr[0] + ":" + in_zeros + ":" + addr[1]

        ret = []
        for a in addr.split(":"):
            ret.append(a.rjust(4, '0'))

        ret = ":".join(ret)

        if mask is not None:
            ret += "/" + mask

        return ret

    def dropZeros(self, addr):
        prefix = []
        for a in reversed(addr.split(":")):
            if a == "0000" and prefix == []:
                continue
            prefix.append(a)

        prefix.reverse()
        return ":".join(prefix)

    def prefixMatchAddress(self, prefix, addr):
        if prefix is None:
            return False

        aprefix, amask = self.splitAddressMask(prefix)
        aprefix = self.dropZeros(aprefix)

        if len(aprefix) > len(addr):
            return False

        plen = len(aprefix)

        return aprefix[:plen] == addr[:plen]

    def getPrefix(self, addr, mask=None):
        if "::" in addr:
            return addr.split("::")[0]

        if mask is not None:
            mask = int(float(mask))

        if ":" in addr:
            if mask is None:
                mask = 64
            addr_list = addr.split(":")[:mask/16]
            return ":".join(addr_list)

        if "." in addr:
            if mask is None:
                mask = 24
            addr_list = addr.split(".")[:mask/8]
            return ".".join(addr_list)

    def isIpv6(self, addr):
        if addr is None:
            return False
        return ':' in addr

    def isIpv4(self, addr):
        if addr is None:
            return False
        return '.' in addr and not any(c.isalpha() for c in addr)

    def isIpAddress(self, addr):
        if addr is None:
            return False
        return self.isIpv4(addr) or self.isIpv6(addr)

    def isMulticast(self, addr):
        if addr is None:
            return False
        return False

    def splitAddressMask(self, ipmask):
        if '/' in ipmask:
            addr, mask = ipmask.split("/")
        else:
            addr = ipmask
            if self.isIpv6(ipmask):
                mask = 64     # By default we give mask of 64
            else:
                mask = 24

        if self.isIpv6(addr):
            addr = self.paddingZeros(addr)

        return (addr, mask)

    def MAC48toEUI64(self, mac):
        addr = mac.split(":")
        if len(addr) != 6:
            return None
        addr.insert(3, 'fe')
        addr.insert(3, 'ff')
        eui = "-".join(addr)
        return eui

    def EUI64toIID(self, addr):
        int_addr = addr

        if type(addr) == str:
            int_addr = self.eui64_string_to_int(addr)

        if int_addr >= 65536:
            if (1 << 57) > int_addr:
                int_addr = (1 << 57) | int_addr
            else:
                int_addr = int_addr | (1 << 57)

        if type(addr) == str:
            iid_addr = self.int_to_ipv6_addr_string(int_addr)

        return iid_addr

    def IIDtoEUI64(self, addr):
        eui_addr = addr

        if type(addr) == str:
            eui_addr = self.ipv6_addr_string_to_int(addr)

        eui_addr = ~pow(2, 57) & eui_addr

        if type(addr) == str:
            eui_addr = self.int_to_eui64_string(eui_addr)

        return eui_addr

    def mac48_string_to_int(self, hw_addr):
        res = "0x"
        for i in hw_addr.split(":"):
            for x in range(2 - len(i)):
                res += "0"
            res += i
        res = int(res, 16)
        return res

    def eui64_string_to_int(self, eui_addr):
        res = "0x"
        for i in eui_addr.split("-"):
            for x in range(2 - len(i)):
                res += "0"
            res += i
        res = int(res, 16)
        return res

    def ipv6_addr_string_to_int(self, ipv6_addr):
        res = "0x"
        for i in ipv6_addr.split(":"):
            for x in range(4 - len(i)):
                res += "0"
            res += i
        res = int(res, 16)
        return res

    def int_to_eui64_string(self, int_val):
        res = hex(int_val)
        res = str(res)
        if res[-1] == "L":
            res = res[:-1]

        if res[:2] == "0x":
            res = res[2:]

        while len(res) < 16:
            res = "0" + res

        res = [res[i:i+2] for i in range(0, len(res), 2)]
        res = "-".join(res)
        return str(res)

    def int_to_mac48_string(self, int_val):
        res = hex(int_val)
        res = str(res)
        if res[-1] == "L":
            res = res[:-1]

        if res[:2] == "0x":
            res = res[2:]

        while len(res) < 12:
            res = "0" + res

        res = [res[i:i+2] for i in range(0, len(res), 2)]
        res = ":".join(res)
        return str(res)

    def int_to_ipv6_addr_string(self, int_val):
        res = hex(int_val)
        res = str(res)
        if res[-1] == "L":
            res = res[:-1]

        if res[:2] == "0x":
            res = res[2:]

        while len(res) < 16:
            res = "0" + res

        res = [res[i:i+4] for i in range(0, len(res), 4)]
        res = ":".join(res)
        return str(res)

    def isDomainName(self, domain):
        return "." in domain and not self.isIpv4(domain)

    def getHostByName(self, name):
        ip = socket.gethostbyname(name)
        return ip
