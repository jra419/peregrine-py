import os
import pickle
import itertools
import numpy as np
import pandas as pd
from pathlib import Path
from fc_kitnet import FCKitNET
from plugins.KitNET.KitNET import KitNET

LAMBDAS = 4
LEARNING_RATE = 0.1
HIDDEN_RATIO = 0.75

class PipelineKitNET:
    def __init__(
            self, trace, labels, sampling, fm_grace, ad_grace, max_ae, fm_model, el_layer,
            ol_layer, train_stats, attack, train_exact_ratio, save_stats_global):

        self.decay_to_pos = {
            0: 0, 1: 0, 2: 1, 3: 2, 4: 3,
            8192: 1, 16384: 2, 24576: 3}

        self.fm_grace = fm_grace
        self.ad_grace = ad_grace
        self.attack = attack
        self.m = max_ae
        self.sampling_rate = sampling
        self.train_exact_ratio = train_exact_ratio
        self.save_stats_global = save_stats_global

        self.stats_global = []
        self.rmse_list = []
        self.peregrine_eval = []

        self.threshold = 0
        self.pkt_cnt_global = 0
        self.train_skip = False

        self.df_train_stats_list = []
        self.df_exec_stats_list = []

        # Read the csv containing the ground truth labels.
        self.trace_labels = pd.read_csv(labels, header=None)

        if fm_model is not None and \
                el_layer is not None and \
                ol_layer is not None and \
                train_stats is not None:
            self.train_skip = True

        # If train_skip is true, import the previously generated models.
        if self.train_skip:
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

        # Initialize KitNET.
        self.kitnet = KitNET(
            80, max_ae, fm_grace, ad_grace, LEARNING_RATE, HIDDEN_RATIO, fm_model, el_layer,
            ol_layer, attack, train_exact_ratio)

        # Initialize feature extraction/computation.
        self.fc = FCKitNET(trace, sampling, fm_grace+ad_grace, self.train_skip)

        self.trace_size = self.fc.trace_size()

    def process(self):
        # Process the trace, packet by packet.
        while True:
            cur_stats = 0

            if not self.train_skip:
                if len(self.rmse_list) % 1000 == 0 and \
                        len(self.rmse_list) < self.fm_grace + self.ad_grace:
                    print(f'Processed pkts: {len(self.rmse_list)}')
                elif self.pkt_cnt_global % 1000 == 0 and \
                    len(self.rmse_list) >= self.fm_grace + self.ad_grace:
                    print(f'Processed pkts: {self.fm_grace + self.ad_grace + self.pkt_cnt_global}')
            else:
                if self.pkt_cnt_global % 1000 == 0:
                    print(f'Processed pkts: {self.fm_grace + self.ad_grace + self.pkt_cnt_global}')

            # Training phase.
            if len(self.rmse_list) < (self.train_exact_ratio * (self.fm_grace + self.ad_grace)) \
                    and not self.train_skip:
                self.fc.feature_extract()
                cur_stats = self.fc.process_exact('training')
            elif len(self.rmse_list) < self.fm_grace + self.ad_grace and not self.train_skip:
                self.fc.feature_extract()
                cur_stats = self.fc.process('training')

            # Execution phase.
            else:
                self.pkt_cnt_global += 1
                self.fc.feature_extract()
                cur_stats = self.fc.process('execution')

            # If any statistics were obtained, send them to the ML pipeline.
            # Execution phase: only proceed according to the sampling rate.
            if cur_stats != 0:
                # Break when we reach the end of the trace file.
                if self.fm_grace + self.ad_grace + self.pkt_cnt_global == self.trace_size:
                    break
                if self.pkt_cnt_global % self.sampling_rate != 0:
                    continue


                # Flatten the statistics' list of lists.
                cur_stats = list(itertools.chain(*cur_stats))

                if self.save_stats_global:
                    self.stats_global.append(cur_stats)

                # Update the stored global stats with the latest packet stats.
                input_stats = self.update_stats(cur_stats)
                # Call function with the content of kitsune's main (before the eval/csv part).
                rmse = self.kitnet.process(input_stats)

                self.rmse_list.append(rmse)
                try:
                    self.peregrine_eval.append([
                        cur_stats[0], cur_stats[1], cur_stats[2],
                        cur_stats[3], cur_stats[4], cur_stats[5],
                        rmse, self.trace_labels.iat[
                            self.fm_grace + self.ad_grace + self.pkt_cnt_global - 1, 0]])
                except IndexError:
                    print(self.trace_labels.shape[0])
                    print(self.pkt_cnt_global)
                    print(self.fm_grace + self.ad_grace + self.pkt_cnt_global - 1)

                # At the end of the training phase, store the highest rmse value as the threshold.
                # Also, save the stored stat values.
                if not self.train_skip and len(self.rmse_list) == self.fm_grace + self.ad_grace:
                    self.threshold = max(self.rmse_list, key=float)
                    self.save_train_stats()
                    print('Starting execution phase...')

                # Break when we reach the end of the trace file.
                elif self.fm_grace + self.ad_grace + self.pkt_cnt_global == self.trace_size:
                    self.save_exec_stats()
                    break
            else:
                print('TIMEOUT.')
                break

    def update_stats(self, cur_stats):

        cur_decay_pos = self.decay_to_pos[cur_stats[6]]

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

        if len(self.df_train_stats_list) < self.fm_grace + self.ad_grace:
            self.df_train_stats_list.append(input_stats)
        else:
            self.df_exec_stats_list.append(input_stats)

        return input_stats


    def save_train_stats(self):
        train_stats = [
            self.stats_mac_ip_src, self.stats_ip_src,
            self.stats_ip, self.stats_five_t]

        outdir = str(Path(__file__).parents[0]) + '/plugins/KitNET/models'
        if not os.path.exists(str(Path(__file__).parents[0]) + '/plugins/KitNET/models'):
            os.mkdir(outdir)

        with open(outdir + '/' + self.attack + '-m-' + str(self.m)
                  + '-r-' + str(self.train_exact_ratio) + '-train-stats'
                  + '.txt', 'wb') as f_stats:
            pickle.dump(train_stats, f_stats)

        for i in range(0, len(self.df_train_stats_list), 50000):
            self.df_train_stats_list[i:i + 50000]
            df_train_stats = pd.DataFrame(self.df_train_stats_list[i:i + 50000])
            df_train_stats.to_pickle(
                f'{outdir}/{self.attack}-m-{self.m}-r-'
                f'{self.train_exact_ratio}-train-full-{int(i/50000)}.pkl')

        outdir_params = f'{Path(__file__).parents[0]}/plugins/KitNET/models/spatial/{self.attack}'\
                        f'-m-{self.m}-r-{self.train_exact_ratio}/params'
        if not os.path.exists(outdir_params):
            os.makedirs(outdir_params)
        outdir_norms = f'{Path(__file__).parents[0]}/plugins/KitNET/models/spatial/{self.attack}'\
                       f'-m-{self.m}-r-{self.train_exact_ratio}/norms'
        if not os.path.exists(outdir_norms):
            os.makedirs(outdir_norms)
        outdir_maps = f'{Path(__file__).parents[0]}/plugins/KitNET/models/spatial/{self.attack}'\
                      f'-m-{self.m}-r-{self.train_exact_ratio}/maps'
        if not os.path.exists(outdir_maps):
            os.makedirs(outdir_maps)

        for i in range(len(self.kitnet.ensembleLayer)):
            pd.DataFrame(self.kitnet.ensembleLayer[i].W).to_csv(
                f'{outdir_params}/L{i}_W.csv', header=False, index=False)
            pd.DataFrame(self.kitnet.ensembleLayer[i].hbias).to_csv(
                f'{outdir_params}/L{i}_B1.csv', header=False, index=False)
            pd.DataFrame(self.kitnet.ensembleLayer[i].vbias).to_csv(
                f'{outdir_params}/L{i}_B2.csv', header=False, index=False)
            pd.DataFrame(self.kitnet.ensembleLayer[i].norm_min).to_csv(
                f'{outdir_norms}/L{i}_NORM_MIN.csv', header=False, index=False)
            pd.DataFrame(self.kitnet.ensembleLayer[i].norm_max).to_csv(
                f'{outdir_norms}/L{i}_NORM_MAX.csv', header=False, index=False)

        pd.DataFrame(self.kitnet.outputLayer.W).to_csv(
            f'{outdir_params}/OUTL_W.csv', header=False, index=False)
        pd.DataFrame(self.kitnet.outputLayer.hbias).to_csv(
            f'{outdir_params}/OUTL_B1.csv', header=False, index=False)
        pd.DataFrame(self.kitnet.outputLayer.vbias).to_csv(
            f'{outdir_params}/OUTL_B2.csv', header=False, index=False)
        pd.DataFrame(self.kitnet.outputLayer.norm_min).to_csv(
            f'{outdir_norms}/OUTL_NORM_MIN.csv', header=False, index=False)
        pd.DataFrame(self.kitnet.outputLayer.norm_max).to_csv(
            f'{outdir_norms}/OUTL_NORM_MAX.csv', header=False, index=False)

        for i in range(len(self.kitnet.v)):
            pd.DataFrame(self.kitnet.v[i]).T.to_csv(
                f'{outdir_maps}/L{i}_MAP.csv', header=False, index=False)
            pd.DataFrame([len(self.kitnet.v[i]),
                          int(np.ceil(len(self.kitnet.v[i])*0.75))]).T.to_csv(
                            f'{outdir_maps}/L{i}_NEURONS.csv', header=False, index=False)

        pd.DataFrame([len(self.kitnet.v)]).T.to_csv(
            f'{outdir_maps}/N_LAYERS.csv', header=False, index=False)

    def save_exec_stats(self):
        outdir = str(Path(__file__).parents[0]) + '/plugins/KitNET/models'
        if not os.path.exists(str(Path(__file__).parents[0]) + '/plugins/KitNET/models'):
            os.mkdir(outdir)

        for i in range(0, len(self.df_exec_stats_list), 50000):
            self.df_exec_stats_list[i:i + 50000]
            df_exec_stats = pd.DataFrame(self.df_exec_stats_list[i:i + 50000])
            df_exec_stats.to_pickle(
                f'{outdir}/{self.attack}-m-{self.m}-r-'
                f'{self.train_exact_ratio}-exec-full-{int(i/50000)}.pkl')

    def reset_stats(self):
        print('Reset stats')

        self.stats_mac_ip_src = {}
        self.stats_ip_src = {}
        self.stats_ip = {}
        self.stats_five_t = {}
