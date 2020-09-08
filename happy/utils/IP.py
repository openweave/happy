#!/usr/bin/env python3

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

from __future__ import absolute_import
import socket
from six.moves import range


class IP:
    @staticmethod
    def getIPv6Subnet(addr):
        a = addr.split(":")

        if len(a) > 3:
            return int(float(a[3]))
        else:
            None

    @staticmethod
    def getIPv6IID(addr):
        a = addr.split(":")

        if len(a) == 8:
            return str(":".join(a[4:]))
        else:
            return None

    @staticmethod
    def paddingZeros(addr_mask):
        if not IP.isIpv6(addr_mask):
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

    @staticmethod
    def dropZeros(addr):
        prefix = []
        for a in reversed(addr.split(":")):
            if a == "0000" and prefix == []:
                continue
            prefix.append(a)

        prefix.reverse()
        return ":".join(prefix)

    @staticmethod
    def prefixMatchAddress(prefix, addr):
        """This function attempts to match the specified network prefix against the provided address.

        Args:
           prefix (str): A string containing the IPv4 or IPv6 prefix, in slash notation, to match against 'addr'.
           addr (str): A string containing the IPv4 or IPv6 address against which 'prefix' will be matched.

        Returns:
           bool. The return code::

              True  -- The prefix matches the address.
              False -- The prefix does not match the address.
        """

        # If there is no prefix, then the match can never succeed.

        if prefix is None:
            return False

        # Split the address into prefix and mask portions.
        
        aprefix, amask = IP.splitAddressMask(prefix)

        # Ensure like address families are being compared between the
        # prefix and address. If not, the match can never succeed.

        if ((IP.isIpv4(aprefix) and not IP.isIpv4(addr)) or
            (IP.isIpv6(aprefix) and not IP.isIpv6(addr))):
            return False

        # Perform address family-specific matching.

        if (IP.isIpv6(aprefix)):
            return IP.__ipv6PrefixMatchAddress(aprefix, amask, addr)
        elif (IP.isIpv4(aprefix)):
            return IP.__ipv4PrefixMatchAddress(aprefix, amask, addr)
        else:
            return False


    @staticmethod
    def __ipv4PrefixMatchAddress(prefix, mask, addr):
        # First, canonicalize the address and prefix

        prefix = IP.__ipv4Canonicalize(prefix)

        addr = IP.__ipv4Canonicalize(addr)

        # Then, to check for a match, convert the prefix, mask, and
        # address into binary values and check that the logical and of
        # the prefix with the mask matches the logical and of the
        # address and the mask.

        bmask = IP.__ipv4MaskStringToBinary(mask)

        bprefix = IP.__ipv4AddressStringToBinary(prefix)

        baddr = IP.__ipv4AddressStringToBinary(addr)

        matched = ((bprefix & bmask) == (baddr & bmask))

        return matched


    @staticmethod
    def __ipv6PrefixMatchAddress(prefix, mask, addr):
        prefix = IP.dropZeros(prefix)

        if len(prefix) > len(addr):
            return False

        plen = len(prefix)

        return prefix[:plen] == addr[:plen]


    @staticmethod
    def __ipv4Canonicalize(addr):
        """This function attempts to canonicalize an IPv4 address (four completely-specified octets) or prefix (less than four octets) into a four octet, dotted decimal string representation by appending the appropriate number of zeroes (.0) to the address. Note, an empty string is canonicalized into the any address (0.0.0.0).

        Args:
           addr (str): A string containing the IPv4 address or prefix to canonicalize

        Returns:
           str. The canonicalized IPv4 address or prefix.
        """
        
        if len(addr) > 0:
            octets = addr.count(".") + 1
        else:
            octets = 0

        missing = 4 - octets

        if missing > 0:
            padding = ".".join(["0"] * missing)
            if octets > 0:
                addr += "." + padding
            else:
                addr += padding

        return addr


    @staticmethod
    def __ipv4AddressStringToBinary(addr):
        baddr = 0
        
        for index, octet in list(enumerate(reversed(addr.split(".")))):
            baddr = baddr + ((int(octet) & 0xFF) << (index * 8))

        return baddr


    @staticmethod
    def __ipv4MaskStringToBinary(mask):
        bmask = ((2**32) - 1) ^ ((2**32) - 1) >> int(mask)

        return bmask


    @staticmethod
    def getPrefix(addr, mask=None):
        if "::" in addr:
            return addr.split("::")[0]

        if mask is not None:
            mask = int(float(mask))

        if ":" in addr:
            if mask is None:
                mask = 64
            addr_list = addr.split(":")[:mask//16]
            return ":".join(addr_list)

        if "." in addr:
            if mask is None:
                mask = 24
            addr_list = addr.split(".")[:mask//8]
            return ".".join(addr_list)

    @staticmethod
    def isIpv6(addr):
        if addr is None:
            return False
        return ':' in addr

    @staticmethod
    def isIpv4(addr):
        if addr is None:
            return False
        return '.' in addr and not any(c.isalpha() for c in addr)

    @staticmethod
    def isIpAddress(addr):
        if addr is None:
            return False
        return IP.isIpv4(addr) or IP.isIpv6(addr)

    @staticmethod
    def isMulticast(addr):
        if addr is None:
            return False
        return False

    @staticmethod
    def splitAddressMask(ipmask):
        if '/' in ipmask:
            addr, mask = ipmask.split("/")
        else:
            addr = ipmask
            if IP.isIpv6(ipmask):
                mask = 64     # By default we give mask of 64
            else:
                mask = 24

        if IP.isIpv6(addr):
            addr = IP.paddingZeros(addr)

        return (addr, mask)

    @staticmethod
    def MAC48toEUI64(mac):
        addr = mac.split(":")
        if len(addr) != 6:
            return None
        addr.insert(3, 'fe')
        addr.insert(3, 'ff')
        eui = "-".join(addr)
        return eui

    @staticmethod
    def EUI64toIID(addr):
        int_addr = addr

        if type(addr) == str:
            int_addr = IP.eui64_string_to_int(addr)

        if int_addr >= 65536:
            if (1 << 57) > int_addr:
                int_addr = (1 << 57) ^ int_addr
            else:
                int_addr = int_addr ^ (1 << 57)

        if type(addr) == str:
            iid_addr = IP.int_to_ipv6_addr_string(int_addr)

        return iid_addr

    @staticmethod
    def IIDtoEUI64(addr):
        eui_addr = addr

        if type(addr) == str:
            eui_addr = IP.ipv6_addr_string_to_int(addr)

        eui_addr = pow(2, 57) ^ eui_addr

        if type(addr) == str:
            eui_addr = IP.int_to_eui64_string(eui_addr)

        return eui_addr

    @staticmethod
    def mac48_string_to_int(hw_addr):
        res = "0x"
        for i in str(hw_addr).split(":"):
            for x in range(2 - len(i)):
                res += "0"
            res += i
        res = int(res, 16)
        return res

    @staticmethod
    def eui64_string_to_int(eui_addr):
        res = "0x"
        for i in eui_addr.split("-"):
            for x in range(2 - len(i)):
                res += "0"
            res += i
        res = int(res, 16)
        return res

    @staticmethod
    def ipv6_addr_string_to_int(ipv6_addr):
        res = "0x"
        for i in ipv6_addr.split(":"):
            for x in range(4 - len(i)):
                res += "0"
            res += i
        res = int(res, 16)
        return res

    @staticmethod
    def int_to_eui64_string(int_val):
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

    @staticmethod
    def int_to_mac48_string(int_val):
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

    @staticmethod
    def int_to_ipv6_addr_string(int_val):
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

    @staticmethod
    def isDomainName(domain):
        return "." in domain and not IP.isIpv4(domain)

    @staticmethod
    def getHostByName(name):
        ip = socket.gethostbyname(name)
        return ip
