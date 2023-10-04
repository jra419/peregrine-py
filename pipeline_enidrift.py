import itertools
import numpy as np
from fc_enidrift import FCENIDrift
from plugins.ENIDrift.ENIDrift_main import ENIDrift_train

LAMBDAS = 4

class PipelineENIDrift:
    def __init__(
            self, trace, labels, sampling, attack, hypr, delta, incr,
            release_speed, save_stats_global):

        self.attack = attack
        self.sampling_rate = sampling
        self.hypr = hypr
        self.delta = delta
        self.incr = incr
        self.release_speed = release_speed
        self.save_stats_global = save_stats_global

        self.stats_global = []
        self.prediction = []
        self.peregrine_eval = []

        self.threshold = 0
        self.pkt_cnt_global = 0
        self.train_skip = False

        # Read the csv containing the ground truth labels.
        # self.trace_labels = pd.read_csv(labels, header=None)
        self.trace_labels_global = np.genfromtxt(labels, dtype='i4')
        self.trace_labels = []

        self.stats_mac_ip_src = {}
        self.stats_ip_src = {}
        self.stats_ip = {}
        self.stats_five_t = {}

        # Initialize ENIDrift.
        self.enidrift = ENIDrift_train(
            hypr=self.hypr, delta=self.delta, incremental=self.incr)

        # Initialize feature extraction/computation.
        self.fc = FCENIDrift(trace, sampling)

        self.trace_size = self.fc.trace_size()

    def process(self):
        trace_labels_cur = []
        cur_pkt = 0

        # Process the trace, packet by packet.
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
                if self.pkt_cnt_global % self.sampling_rate != 0:
                    continue

                cur_pkt += 1
                trace_labels_cur.append(self.trace_labels_global[self.pkt_cnt_global-1])
                # Flatten the statistics' list of lists.
                cur_stats = list(itertools.chain(*cur_stats))

                if self.save_stats_global:
                    self.stats_global.append(cur_stats)

                # Update the stored global stats with the latest packet stats.
                input_stats = self.update_stats(cur_stats)

                # ENIDrift's ensemble detection.
                prediction = self.enidrift.predict(input_stats.reshape(1, -1))

                # ENIDrift's sub-classifier generation.
                if cur_pkt % self.release_speed == 0:
                    print(f'pkt_cnt_global: {self.pkt_cnt_global}')
                    print(f'cur_pkt: {cur_pkt}')
                    print(f'release_speed: {self.release_speed}')
                    self.enidrift.update(np.array(trace_labels_cur))
                    trace_labels_cur = []

                self.prediction.append(prediction[0])
                self.trace_labels.append(self.trace_labels_global[self.pkt_cnt_global-1])

                try:
                    self.peregrine_eval.append([
                        cur_stats[0], cur_stats[1], cur_stats[2], cur_stats[3], cur_stats[4],
                        cur_stats[5], prediction[0], prediction[1], prediction[2],
                        self.trace_labels_global[self.pkt_cnt_global - 1]])
                except IndexError:
                    print(self.trace_labels.shape[0])
                    print(self.pkt_cnt_global)
                    print(self.pkt_cnt_global - 1)
            else:
                print('TIMEOUT.')
                break

        return [self.prediction, self.stats_global, self.peregrine_eval]

    def update_stats(self, cur_stats):

        decay_to_pos = {
            0: 0, 1: 0, 2: 1, 3: 2, 4: 3,
            8192: 1, 16384: 2, 24576: 3}
        cur_decay_pos = decay_to_pos[cur_stats[6]]

        hdr_mac_ip_src = cur_stats[0] + cur_stats[1]
        hdr_ip_src = cur_stats[1]
        hdr_ip = cur_stats[1] + cur_stats[2]
        hdr_five_t = cur_stats[1] + cur_stats[2] + cur_stats[3] + cur_stats[4] + cur_stats[5]

        if hdr_mac_ip_src not in self.stats_mac_ip_src:
            self.stats_mac_ip_src[hdr_mac_ip_src] = np.zeros(3 * LAMBDAS)
        self.stats_mac_ip_src[hdr_mac_ip_src][(3*cur_decay_pos):(3*cur_decay_pos+3)] = \
            cur_stats[7:10]

        if hdr_ip_src not in self.stats_ip_src:
            self.stats_ip_src[hdr_ip_src] = np.zeros(3 * LAMBDAS)
        self.stats_ip_src[hdr_ip_src][(3*cur_decay_pos):(3*cur_decay_pos+3)] = \
            cur_stats[10:13]

        if hdr_ip not in self.stats_ip:
            self.stats_ip[hdr_ip] = np.zeros(7 * LAMBDAS)
        self.stats_ip[hdr_ip][(7*cur_decay_pos):(7*cur_decay_pos+7)] = \
            cur_stats[13:20]

        if hdr_five_t not in self.stats_five_t:
            self.stats_five_t[hdr_five_t] = np.zeros(7 * LAMBDAS)
        self.stats_five_t[hdr_five_t][(7*cur_decay_pos):(7*cur_decay_pos+7)] = \
            cur_stats[20:]

        input_stats = np.concatenate((
            self.stats_mac_ip_src[hdr_mac_ip_src],
            self.stats_ip_src[hdr_ip_src],
            self.stats_ip[hdr_ip],
            self.stats_five_t[hdr_five_t]))

        # Convert any existing NaNs to 0.
        input_stats[np.isnan(input_stats)] = 0

        return input_stats
