import itertools
import numpy as np
from fc_whisper import FCWhisper
from scapy.all import *
from utils.peregrine_hdr import WhisperPeregrineHdr
import time

class PipelineWhisper:
    def __init__(self, trace, labels, sampling, train_size, dst_mac):

        self.sampling_rate = sampling
        self.dst_mac = dst_mac

        self.stats_global = []

        self.threshold = 0
        self.pkt_cnt_global = 0
        self.train_size = train_size

        # Read the csv containing the ground truth labels.
        self.trace_labels_global = np.genfromtxt(labels, dtype='i4')
        self.trace_labels = []

        self.stats_ip_src = {}

        # Initialize Whisper.

        # Initialize feature extraction/computation.
        self.fc = FCWhisper(trace)

        self.trace_size = self.fc.trace_size()

    def process(self):
        # Process the trace, packet by packet.
        s = conf.L2socket('enp1s0')
        while True:
            cur_stats = 0

            if self.pkt_cnt_global % 1000 == 0:
                print(f'Processed pkts: {self.pkt_cnt_global}')

            self.pkt_cnt_global += 1
            self.fc.feature_extract()
            cur_stats = self.fc.process()

            # If any statistics were obtained, send them to the ML pipeline.
            # Proceed according to the sampling rate.
            if cur_stats != 0:
                if self.pkt_cnt_global == self.trace_size:
                    break
                if (self.pkt_cnt_global % self.sampling_rate != 0
                        and self.pkt_cnt_global > self.train_size):
                    continue

                # Flatten the statistics' list of lists.
                cur_stats = list(itertools.chain(*cur_stats))
                self.stats_global.append(cur_stats)

                # Generate pkt w/ peregrine custom hdr and send it to Whisper.
                s.send(
                    Ether(dst=self.dst_mac, src=cur_stats[2])/
                    IP(src=cur_stats[3],dst=cur_stats[4],proto=253)/
                    WhisperPeregrineHdr(
                        ip_src=cur_stats[8], ip_proto=int(cur_stats[9]),
                        length=int(cur_stats[10]), timestamp=cur_stats[11])
                    )
            else:
                print('TIMEOUT.')
                break

        return [self.stats_global]
