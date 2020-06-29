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
#       Implements HappyPacketProcess class that sniffer packet and inject the specifc packet with tcp-reject,
#       the fitler rule could be with dst ip or ip list(source ip and dest ip)
#       python HappyPacketProcess.py  --interface "wlan0" --action "RESET" --ips "107.22.61.55,10.0.1.2" --start "2" --duration 6
#       python HappyPacketProcess.py  --interface "wlan0" --action "RESET" --dstPort "11095" --start "2" --duration "20"
#
#

from __future__ import absolute_import
from __future__ import print_function
from datetime import datetime
import getopt
import logging
import multiprocessing
import os
import socket
import random
from struct import *
import signal
import sys
import time
from six.moves import range

options = {}
options['interface'] = None
options['quiet'] = False
options['action'] = None
options['ips'] = None
options['dstPort'] = None
options['start'] = None
options['duration'] = None


def MergeDicts(*dictArguments):
    merged = {}
    for i in dictArguments:
        merged.update(i)
    return merged


def CheckSumCalculation(value):
    checkSum = 0
    for i in range(0, len(value), 2):
        checkSum += (ord(value[i]) << 8) + (ord(value[i + 1]))
    return ~((checkSum >> 16) + (checkSum & 0xffff)) & 0xffff


class EthernetFrame(object):
    def __init__(self):
        self.ethProto = 0
        self.ethDest = 0
        self.ethSource = 0
        self.payload = 0
        self.parent = None

    def Decode(self, packet):
        ethLength = 14
        ethHeader = packet[:ethLength]
        eth = unpack('!6s6sH', ethHeader)
        self.ethProto = socket.ntohs(eth[2])
        self.ethDest = self.GetEthernetAddr(packet[0:6])
        self.ethSource = self.GetEthernetAddr(packet[6:12])
        self.payload = packet[ethLength:]
        self.parent = self

    def Encode(self):
        eth = pack('!6s6sH', self.ethDest, self.ethSource, self.ethProto)
        return eth

    def GetEthernetAddr(self, addr):
        return "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % \
               (ord(addr[0]), ord(addr[1]), ord(addr[2]), ord(addr[3]), ord(addr[4]), ord(addr[5]))

    def GetEthernetHeaderDic(self):
        return {'ethProto': self.ethProto, 'ethDest': self.ethDest, 'ethSource': self.ethSource}

    def GetPayload(self):
        return self.payload

    def GetParent(self):
        return self.parent


class IPv4Packet(object):
    def __init__(self):
        self.ipVersionIhl = 0
        self.ipVersion = 0
        self.ipIhl = 0
        self.ipTos = 0
        self.ipLen = 0
        self.ipId = 0
        self.ipOff = 0
        self.ipTTL = 0
        self.ipProtocol = 0
        self.ipSum = 0
        self.ipSrc = 0
        self.ipDst = 0
        self.payload = 0
        self.parent = None

    def Decode(self, packet):
        ipHeader = packet[0:20]
        iph = unpack('!BBHHHBBH4s4s', ipHeader)
        self.ipVersionIhl = iph[0]
        self.ipVersion = self.ipVersionIhl >> 4
        self.ipIhl = self.ipVersionIhl & 0xF
        iphLength = self.ipIhl * 4
        self.ipTos = iph[1]
        self.ipLen = iph[2]
        self.ipId = iph[3]
        self.ipOff = iph[4]
        self.ipTTL = iph[5]
        self.ipProtocol = iph[6]
        self.ipSum = iph[7]
        self.ipSrc = socket.inet_ntoa(iph[8])
        self.ipDst = socket.inet_ntoa(iph[9])
        self.payload = packet[iphLength:]
        self.parent = self

    def Encode(self):
        ipHeader = pack('!BBHHHBBH4s4s',
                        self.ipVersionIhl,
                        self.ipTos,
                        self.ipLen,
                        self.ipId,
                        self.ipOff,
                        self.ipTTL,
                        self.ipProtocol,
                        self.ipSum,
                        socket.inet_aton(str(self.ipSrc)),
                        socket.inet_aton(str(self.ipDst))
                        )
        return ipHeader

    def GetIpv4HeaderDic(self):
        return {'ipVersion': self.ipVersion, 'ipIhl': self.ipIhl, 'ipTos': self.ipTos,
                'ipLen': self.ipLen, 'ipId': self.ipId, 'ipOff': self.ipOff, 'ipTTL': self.ipTTL,
                'ipProtocol': self.ipProtocol, 'ipSum': self.ipSum, 'ipSrc': self.ipSrc, 'ipDst': self.ipDst}

    def GetPayload(self):
        return self.payload

    def GetParent(self):
        return self.parent

    def SetIpVersionIhl(self, value):
        self.ipVersionIhl = value

    def SetIpTos(self, value):
        self.ipTos = value

    def SetIpLen(self, value):
        self.ipLen = value

    def SetIpId(self, value):
        self.ipId = value

    def SetIpOff(self, value):
        self.ipOff = value

    def SetIpTTL(self, value):
        self.ipTTL = value

    def SetIpProtocol(self, value):
        self.ipProtocol = value

    def SetIpSum(self, value):
        self.ipSum = CheckSumCalculation(value)

    def SetIpSrc(self, value):
        self.ipSrc = value

    def SetIpDst(self, value):
        self.ipDst = value


class TCPPacket(object):
    def __init__(self):
        self.tcpSrcPort = 0
        self.tcpDestPort = 0
        self.tcpSeq = 0
        self.tcpAckSeq = 0
        self.tcpDoffReserved = 0
        self.tcpFlags = 0
        self.tcpFinBit = 0
        self.tcpSynBit = 0
        self.tcpRstBit = 0
        self.tcpPshBit = 0
        self.tcpAckBit = 0
        self.tcpUrgBit = 0
        self.tcpWindow = 0
        self.tcpCheck = 0
        self.tcpUrg = 0
        self.payload = 0
        self.parent = None

    def Decode(self, packet):
        tcpHeader = packet[0: 20]
        tcph = unpack('!HHLLBBHHH', tcpHeader)
        self.tcpSrcPort = tcph[0]
        self.tcpDestPort = tcph[1]
        self.tcpSeq = tcph[2]
        self.tcpAckSeq = tcph[3]
        self.tcpDoffReserved = tcph[4]
        self.tcpFlags = tcph[5]
        self.tcpFinBit = self.GetXBit(self.tcpFlags, 0)
        self.tcpSynBit = self.GetXBit(self.tcpFlags, 1)
        self.tcpRstBit = self.GetXBit(self.tcpFlags, 2)
        self.tcpPshBit = self.GetXBit(self.tcpFlags, 3)
        self.tcpAckBit = self.GetXBit(self.tcpFlags, 4)
        self.tcpUrgBit = self.GetXBit(self.tcpFlags, 5)
        tcphLength = self.tcpDoffReserved >> 4
        self.tcpWindow = tcph[6]
        self.tcpCheck = tcph[7]
        self.tcpUrg = tcph[8]
        self.payload = packet[tcphLength * 4:]
        self.parent = self

    def GetXBit(self, n, k):
        return (n & (1 << k)) >> k

    def Encode(self):
        tcpHeader = pack('!HHLLBBHHH', self.tcpSrcPort, self.tcpDestPort, self.tcpSeq, self.tcpAckSeq,
                         self.tcpDoffReserved, self.tcpFlags, self.tcpWindow, self.tcpCheck, self.tcpUrg)
        return tcpHeader

    def GetTcpHeaderDic(self):
        return {"tcpSrcPort": self.tcpSrcPort, "tcpDestPort": self.tcpDestPort, "tcpSeq": self.tcpSeq,
                "tcpAckSeq": self.tcpAckSeq, "tcpDoffReserved": self.tcpDoffReserved, "tcpFlags": self.tcpFlags,
                "tcpFinBit": self.tcpFinBit, "tcpSynBit": self.tcpSynBit, "tcpRstBit": self.tcpRstBit,
                "tcpPshBit": self.tcpPshBit, "tcpAckBit": self.tcpAckBit, "tcpUrgBit": self.tcpUrgBit,
                "tcpWindow": self.tcpWindow, "tcpCheck": self.tcpCheck, "tcpUrg": self.tcpUrg}

    def GetPayload(self):
        return self.payload

    def GetParent(self):
        return self.parent

    def SetTcpSrcPort(self, value):
        self.tcpSrcPort = value

    def SetTcpDestPort(self, value):
        self.tcpDestPort = value

    def SetTcpSeq(self, value):
        self.tcpSeq = value

    def SetTcpAckSeq(self, value):
        self.tcpAckSeq = value

    def SetTcpDoffReserved(self, value):
        self.tcpDoffReserved = value

    def SetTcpFinBit(self, value):
        self.tcpFinBit = value

    def SetTcpSynBit(self, value):
        self.tcpSynBit = value

    def SetTcpRstBit(self, value):
        self.tcpRstBit = value

    def SetTcpPshBit(self, value):
        self.tcpPshBit = value

    def SetTcpAckBit(self, value):
        self.tcpAckBit = value

    def SetTcpUrgBit(self, value):
        self.tcpUrgBit = value

    def SetTcpFlags(self):
        self.tcpFlags = (self.tcpFinBit) + (self.tcpSynBit << 1) + (self.tcpRstBit << 2) + \
                        (self.tcpPshBit << 3) + (self.tcpAckBit << 4) + (self.tcpUrgBit << 5)

    def SetTcpWindow(self, value):
        self.tcpWindow = value

    def SetTcpCheck(self, value):
        self.tcpCheck = CheckSumCalculation(value)

    def SetTcpUrg(self, value):
        self.tcpUrg = value


class Filter(object):
    def __init__(self, packet, options):
        self.options = options
        self.packet = packet
        self.dispatcher = [self.FilterDestinationPort,
                           self.FilterIps,
                           self.FilterTcpRst,
                           self.FilterTcpFin,
                           self.FilterTcpSyn]

    def run(self):
        for filterFunction in self.dispatcher:
            if not filterFunction():
                continue
            else:
                return True
        return False

    def FilterDestinationPort(self):
        if self.options['dstPort'] is not None:
            if options['dstPort'] != self.packet["tcpDestPort"]:
                return True
            else:
                return False
        else:
            return False

    def FilterIps(self):
        if options['ips'] is not None:
            if str(self.packet["ipSrc"]) not in options['ips'] or str(self.packet["ipDst"]) not in options['ips']:
                return True
            else:
                return False
        else:
            return False

    def FilterTcpRst(self):
        if self.packet['tcpRstBit'] == 1:
            return True
        else:
            return False

    def FilterTcpFin(self):
        if self.packet['tcpFinBit'] == 1:
            return True
        else:
            return False

    def FilterTcpSyn(self):
        if self.packet['tcpSynBit'] == 1:
            return True
        else:
            return False


class TimeoutControl():
    class TimeoutControl(Exception):
        pass

    def __init__(self, second):
        self.second = second

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.RaiseException)
        signal.alarm(self.second)

    def __exit__(self, *args):
        signal.alarm(0)

    def RaiseException(self, *args):
        raise TimeoutControl.TimeoutControl()


def Sniffer(packetList, e):
    logger = multiprocessing.get_logger()
    snifferSocket = socket.socket(
        socket.AF_PACKET,
        socket.SOCK_RAW,
        socket.ntohs(0x0003)
    )
    snifferSocket.bind((options['interface'], 0))

    logger.info("Sniffer and process packets, Press Ctrl-C to stop.")

    while True:
        packets = snifferSocket.recvfrom(65535)
        packet = packets[0]
        ethernetFrame = EthernetFrame()
        ethernetFrame.Decode(packet)

        if ethernetFrame.ethProto == 8:
            ipPacket = IPv4Packet()
            ipPacket.Decode(ethernetFrame.payload)

            if ipPacket.ipProtocol == 6:
                tcpPacket = TCPPacket()
                tcpPacket.Decode(ipPacket.payload)
            else:
                continue

        else:
            continue

        packetDic = MergeDicts(ethernetFrame.GetEthernetHeaderDic(), ipPacket.GetIpv4HeaderDic(),
                               tcpPacket.GetTcpHeaderDic())
        logger.debug(packetDic)
        snifferFilter = Filter(packetDic, options)
        if snifferFilter.run() is True:
            continue
        print(packetDic)
        packetList.append(packetDic)
        e.set()

    snifferSocket.close()


def Attack(packetList, e):
    logger = multiprocessing.get_logger()
    attackSocket = socket.socket(
        socket.AF_INET,
        socket.SOCK_RAW,
        socket.IPPROTO_TCP
    )

    attackSocket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    while True:
        e.wait()

        while packetList:
            packet = packetList.pop(0)
            ipPacket = IPv4Packet()
            ihl = 5
            version = 4
            ipPacket.SetIpVersionIhl((version << 4) + ihl)
            ipPacket.SetIpLen(40)
            ipPacket.SetIpId(random.randint(0, 32767))
            ipPacket.SetIpTTL(255)
            ipPacket.SetIpProtocol(socket.IPPROTO_TCP)
            ipPacket.SetIpSrc(packet["ipDst"])
            ipPacket.SetIpDst(packet["ipSrc"])
            ipHeader = ipPacket.Encode()
            ipPacket.SetIpSum(ipHeader)

            tcpPacket = TCPPacket()

            if options["action"] == "RESET":
                tcpPacket.SetTcpDestPort(packet["tcpSrcPort"])
                tcpPacket.SetTcpSrcPort(packet["tcpDestPort"])
                tcpPacket.SetTcpSeq(packet["tcpAckSeq"])
                tcpPacket.SetTcpDoffReserved((5 << 4) + 0)
                tcpPacket.SetTcpRstBit(1)
                tcpPacket.SetTcpFlags()

            logger.info("Attacking {}:{} and {}:{} with {}.".format(
                packet["ipSrc"], packet['tcpSrcPort'],
                packet["ipDst"], packet['tcpDestPort'], options["action"]))
            tcpHeader = tcpPacket.Encode()
            ipSrc = socket.inet_aton(str(packet["ipDst"]))
            ipDst = socket.inet_aton(str(packet["ipSrc"]))
            placeholder = 0
            protocol = socket.IPPROTO_TCP
            tcpLength = len(tcpHeader)

            psudoHeader = pack('!4s4sBBH', ipSrc, ipDst, placeholder, protocol, tcpLength)
            psudoHeader += tcpHeader

            tcpPacket.SetTcpCheck(psudoHeader)

            tcpHeader = tcpPacket.Encode()

            result = ipHeader + tcpHeader

            attackSocket.sendto(result, (str(packet["ipSrc"]), 0))

        e.clear()

    attackSocket.close()


if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hqi:a:s:d:P:",
                                   ["help", "quiet", "interface=", "action=", "ips=", "start=", "duration=",
                                    "dstPort="])

    except getopt.GetoptError as err:
        sys.exit("%s: Failed to parse arguments." % (__file__))

    for o, a in opts:
        if o in ("-h", "--help"):
            print('Implements HappyPacketProcess class that sniffer packet and inject the specifc packet with tcp-reject,' \
                  'the fitler rule could be with dst ip or ip list(source ip and dest ip)' \
                  'python HappyPacketProcess.py  --interface "wlan0" --action "RESET" --ips "107.22.61.55,10.0.1.2" ' \
                  '--start "2" --duration 6 ' \
                  'python HappyPacketProcess.py  --interface "wlan0" --action "RESET" --dstPort "11095" ' \
                  '--start "2" --duration "20"')
            sys.exit(0)

        elif o in ("-q", "--quiet"):
            options["quiet"] = True

        elif o in ("-i", "--interface"):
            options["interface"] = a

        elif o in ("-a", "--action"):
            options["action"] = a

        elif o in ("-p", "--ips"):
            options["ips"] = a.split(',')

        elif o in ("-P", "--dstPort"):
            options["dstPort"] = int(a)

        elif o in ("-s", "--start"):
            options["start"] = int(a)

        elif o in ("-d", "--duration"):
            options["duration"] = int(a)

        else:
            assert False, "unhandled option"

    if os.getuid() != 0:
        print("Please run this program in sudo mode")
        sys.exit(1)

    if options["quiet"]:
        logging.disable(logging.INFO)

    logger = multiprocessing.log_to_stderr(
        level=logging.INFO,
    )

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    logger.info("start at %d seconds, the duration is %d seconds" % (options["start"], options["duration"]))

    time.sleep(options["start"])

    e = multiprocessing.Event()
    manager = multiprocessing.Manager()
    packetList = manager.list()

    sniffer = multiprocessing.Process(
        target=Sniffer,
        args=(packetList, e),
        name='sniffer',
    )
    sniffer.start()

    attack = multiprocessing.Process(
        target=Attack,
        args=(packetList, e),
        name='attack',
    )
    attack.start()

    print(str(datetime.now()))
    try:
        with TimeoutControl(options["duration"]):
            manager.join()
    except Exception:
        sniffer.terminate()
        attack.terminate()
        print(str(datetime.now()))
        pass
