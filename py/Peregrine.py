from KitNET.KitNET import KitNET
import numpy as np

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
                 feature_map=None, ensemble_layer=None, output_layer=None, attack=''):

        self.AnomDetector = KitNET(80, max_autoencoder_size, fm_grace_period,
                                   ad_grace_period, learning_rate, hidden_ratio,
                                   feature_map, ensemble_layer, output_layer, attack)

        self.decay_to_pos = {0: 0,
                             8192: 1,
                             16384: 2,
                             24576: 3}

        self.exec_phase = exec_phase

        self.stats_ip_src = np.zeros((3*lambdas))
        self.stats_mac_src_ip_src = np.zeros((3*lambdas))
        self.stats_ip = np.zeros((7*lambdas))
        self.stats_five_t = np.zeros((7*lambdas))

    def proc_next_packet(self, cur_stats, train_flag):

        if self.exec_phase == 'cp':
            cur_decay_pos = self.decay_to_pos[cur_stats[0] * 8192 - 8192]
        else:
            if train_flag:
                cur_decay_pos = self.decay_to_pos[cur_stats[0] * 8192 - 8192]
            else:
                cur_decay_pos = self.decay_to_pos[cur_stats[0]]

        self.stats_mac_src_ip_src[(3*cur_decay_pos):(3*cur_decay_pos+3)] = cur_stats[1:4]
        self.stats_ip_src[(3*cur_decay_pos):(3*cur_decay_pos+3)] = cur_stats[4:7]
        self.stats_ip[(7*cur_decay_pos):(7*cur_decay_pos+7)] = cur_stats[7:14]
        self.stats_five_t[(7*cur_decay_pos):(7*cur_decay_pos+7)] = cur_stats[14:]

        processed_stats = np.concatenate((self.stats_mac_src_ip_src,
                                          self.stats_ip_src,
                                          self.stats_ip,
                                          self.stats_five_t))

        # Convert any existing NaNs to 0.
        processed_stats[np.isnan(processed_stats)] = 0

        # process KitNET
        # will train during the grace periods, then execute on all the rest.
        return self.AnomDetector.process(processed_stats)
