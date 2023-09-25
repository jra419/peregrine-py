import os
import subprocess
import pandas as pd
import socket
from math import isnan
import crcmod


class FCWhisper:
    def __init__(self, file_path):
        self.file_path = file_path          # Path of the trace file / csv.
        self.df_csv = None                  # Dataframe for the trace csv.
        self.cur_pkt = pd.DataFrame()       # Stats of the packet being processed.
        self.global_pkt_index = 0

        self.ip_src_ts = {}

        # CRC 16 parameters, following the TNA.
        self.crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0x0000, xorOut=0x0000)

        # Hash values for all flow keys.
        self.hash_ip_src = 0

        # Check if the pcap -> csv already exists and pass it to a dataframe.
        self.__check_csv__()

    def __check_csv__(self):
        # Check the file type.
        file_path = self.file_path.split('.')[0]

        if not os.path.isfile(file_path + '.csv'):
            self.parse_pcap(self.file_path)

        self.df_csv = pd.read_csv(file_path + '.csv')

    def trace_size(self):
        return len(self.df_csv)

    def parse_pcap(self, pcap_path):
        fields = "-e frame.time_epoch -e frame.len -e eth.src -e eth.dst \
                    -e ip.src -e ip.dst -e ip.len -e ip.proto -e tcp.srcport \
                    -e tcp.dstport -e udp.srcport -e udp.dstport -e icmp.type \
                    -e icmp.code -e arp.opcode -e arp.src.hw_mac \
                    -e arp.src.proto_ipv4 -e arp.dst.hw_mac -e arp.dst.proto_ipv4 \
                    -e ipv6.src -e ipv6.dst"
        cmd = 'tshark -r ' + pcap_path + ' -T fields ' + \
            fields + ' -E separator=\',\' -E header=y -E occurrence=f > ' + \
            self.file_path.split('.')[0] + '.csv'

        print('Parsing pcap file to csv.')
        subprocess.call(cmd, shell=True)

    def feature_extract(self):
        # Parse the next packet from the csv.
        timestamp = float(self.df_csv.iat[self.global_pkt_index, 0])
        mac_src = str(self.df_csv.iat[self.global_pkt_index, 2])
        pkt_len = self.df_csv.iat[self.global_pkt_index, 6]
        if isnan(pkt_len):
            pkt_len = 0
        ip_src = self.df_csv.iat[self.global_pkt_index, 4]
        if str(ip_src) == 'nan':
            ip_src = '0.0.0.0'
        ip_dst = self.df_csv.iat[self.global_pkt_index, 5]
        if str(ip_dst) == 'nan':
            ip_dst = '0.0.0.0'
        ip_proto = self.df_csv.iat[self.global_pkt_index, 7]
        if isnan(ip_proto):
            ip_proto = 0
        if ip_proto == 17:
            port_src = self.df_csv.iat[self.global_pkt_index, 10]
            port_dst = self.df_csv.iat[self.global_pkt_index, 11]
        elif ip_proto == 6:
            port_src = self.df_csv.iat[self.global_pkt_index, 8]
            port_dst = self.df_csv.iat[self.global_pkt_index, 9]
        else:
            port_src = 0
            port_dst = 0
        if isnan(port_src) or isnan(port_dst):
            port_src = 0
            port_dst = 0

        self.global_pkt_index = self.global_pkt_index + 1
        self.cur_pkt = [
            pkt_len, timestamp, mac_src, ip_src, ip_dst,
            str(int(ip_proto)), str(int(port_src)), str(int(port_dst))]

    def process(self):
        # Hash calculation.
        # CRC16, sliced to 13 bits (0-8191).
        ip_src_bytes = socket.inet_aton(self.cur_pkt[3])

        hash_ip_src_temp = '{:016b}'.format(self.crc16(ip_src_bytes))
        self.hash_ip_src = int(hash_ip_src_temp[-13:], 2)

        # Calculate the 1D/2D statistics for each flow key.

        # 1D: IP src

        # Time interval: difference between cur and last pkt timestamps from the same IP src.
        if self.hash_ip_src in self.ip_src_ts:
            self.ip_src_ts[self.hash_ip_src] = \
                int(self.cur_pkt[1] - self.ip_src_ts[self.hash_ip_src])
        else:
            self.ip_src_ts[self.hash_ip_src] = 0

        cur_stats = [
            self.cur_pkt[3], self.cur_pkt[5], self.cur_pkt[0], self.ip_src_ts[self.hash_ip_src]]

        return [self.cur_pkt, cur_stats]
