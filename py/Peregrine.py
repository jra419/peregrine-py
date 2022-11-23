import os
from KitNET.KitNET import KitNET
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime

# MIT License
#
# Copyright (c) 2018 Yisroel mirsky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


class Peregrine:
    def __init__(self, max_autoencoder_size=10, fm_grace_period=None, ad_grace_period=10000,
                 learning_rate=0.1, hidden_ratio=0.75, lambdas=4, exec_phase='dp',
                 feature_map=None, ensemble_layer=None, output_layer=None, train_stats=None,
                 attack='', train_skip=False):

        self.AnomDetector = KitNET(80, max_autoencoder_size, fm_grace_period,
                                   ad_grace_period, learning_rate, hidden_ratio,
                                   feature_map, ensemble_layer, output_layer, attack)

        self.decay_to_pos = {0: 0, 1: 0, 2: 1, 3: 2, 4: 3,
                             8192: 1, 16384: 2, 24576: 3}

        self.exec_phase = exec_phase
        self.lambdas = lambdas
        self.fm_grace = fm_grace_period
        self.ad_grace = ad_grace_period
        self.attack = attack

        if train_skip:
            with open(train_stats, 'rb') as f_stats:
                stats = pickle.load(f_stats)
                self.stats_mac_ip_src = stats[0]
                self.stats_ip_src = stats[1]
                self.stats_ip = stats[2]
                self.stats_five_t = stats[3]
        else:
            self.stats_mac_ip_src = {}
            self.stats_ip_src = {}
            self.stats_ip = {}
            self.stats_five_t = {}

    def proc_next_packet(self, cur_stats):

        cur_decay_pos = self.decay_to_pos[cur_stats[6]]

        hdr_mac_ip_src = cur_stats[0] + cur_stats[1]
        hdr_ip_src = cur_stats[1]
        hdr_ip = cur_stats[1] + cur_stats[2]
        hdr_five_t = cur_stats[1] + cur_stats[2] + cur_stats[3] + cur_stats[4] + cur_stats[5]

        if hdr_mac_ip_src not in self.stats_mac_ip_src:
            self.stats_mac_ip_src[hdr_mac_ip_src] = np.zeros(3 * self.lambdas)
        self.stats_mac_ip_src[hdr_mac_ip_src][(3*cur_decay_pos):(3*cur_decay_pos+3)] = \
            cur_stats[7:10]

        if hdr_ip_src not in self.stats_ip_src:
            self.stats_ip_src[hdr_ip_src] = np.zeros(3 * self.lambdas)
        self.stats_ip_src[hdr_ip_src][(3*cur_decay_pos):(3*cur_decay_pos+3)] = \
            cur_stats[10:13]

        if hdr_ip not in self.stats_ip:
            self.stats_ip[hdr_ip] = np.zeros(7 * self.lambdas)
        self.stats_ip[hdr_ip][(7*cur_decay_pos):(7*cur_decay_pos+7)] = \
            cur_stats[13:20]

        if hdr_five_t not in self.stats_five_t:
            self.stats_five_t[hdr_five_t] = np.zeros(7 * self.lambdas)
        self.stats_five_t[hdr_five_t][(7*cur_decay_pos):(7*cur_decay_pos+7)] = \
            cur_stats[20:]

        processed_stats = np.concatenate((self.stats_mac_ip_src[hdr_mac_ip_src],
                                          self.stats_ip_src[hdr_ip_src],
                                          self.stats_ip[hdr_ip],
                                          self.stats_five_t[hdr_five_t]))

        # Convert any existing NaNs to 0.
        processed_stats[np.isnan(processed_stats)] = 0

        # process KitNET.
        # will train during the grace periods, then execute on all the rest.
        return self.AnomDetector.process(processed_stats)

    def save_stats(self):

        train_stats = [self.stats_mac_ip_src,
                       self.stats_ip_src,
                       self.stats_ip,
                       self.stats_five_t]

        print(train_stats)

        ts_datetime = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')[:-3]
        outdir = str(Path(__file__).parents[0]) + '/KitNET/models'

        if not os.path.exists(str(Path(__file__).parents[0]) + '/KitNET/models'):
            os.mkdir(outdir)

        with open(outdir + '/' + self.attack + '-' + ts_datetime + '-train-stats' + '.txt', 'wb') as f_stats:
            pickle.dump(train_stats, f_stats)

    def reset_stats(self):
        print('Reset stats')

        self.stats_mac_ip_src = {}
        self.stats_ip_src = {}
        self.stats_ip = {}
        self.stats_five_t = {}
