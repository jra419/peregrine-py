import pandas as pd
from scapy.all import sniff, bind_layers, TCP, UDP, Ether, IP, split_layers
from peregrine_header import PeregrineHdr
from Peregrine import Peregrine
import itertools

# KitNET parameters

learning_rate = 0.1
hidden_ratio = 0.75
# Number of different decay values in the data plane.
lambdas = 4

# List containing the custom header statistics from the last received packet.
cur_stats = []

# List with the complete stats obtained from the data plane.
cur_stats_global = []

# List containing relevant header fields from the last received packet.
pkt_header = []

# List of RMSE classification scores for all incoming packets.
rmse_list = []

# List containing the global eval data. Relevant packet stats + RMSE + ground truth.
peregrine_eval = []

# Data plane-based global packet counter.
# Needed to keep track of the total pkt num, as not all pkts are sent to the control plane.
pkt_cnt_global = 0

# The threshold value is obtained from the highest RMSE score during the training phase.
threshold = 0


def pkt_callback(pkt):
    if PeregrineHdr in pkt:
        global cur_stats
        global pkt_header
        global pkt_cnt_global
        pkt_cnt_global += 1
        cur_stats = [[pkt[PeregrineHdr].decay,
                     pkt[PeregrineHdr].mac_ip_src_pkt_cnt,
                     pkt[PeregrineHdr].mac_ip_src_mean,
                     pkt[PeregrineHdr].mac_ip_src_std_dev,
                     pkt[PeregrineHdr].ip_src_pkt_cnt,
                     pkt[PeregrineHdr].ip_src_mean,
                     pkt[PeregrineHdr].ip_src_std_dev,
                     pkt[PeregrineHdr].ip_pkt_cnt,
                     pkt[PeregrineHdr].ip_mean_0,
                     pkt[PeregrineHdr].ip_std_dev_0,
                     pkt[PeregrineHdr].ip_magnitude,
                     pkt[PeregrineHdr].ip_radius,
                     pkt[PeregrineHdr].ip_sum_res_prod_cov,
                     pkt[PeregrineHdr].ip_pcc,
                     pkt[PeregrineHdr].five_t_pkt_cnt,
                     pkt[PeregrineHdr].five_t_mean_0,
                     pkt[PeregrineHdr].five_t_std_dev_0,
                     pkt[PeregrineHdr].five_t_magnitude,
                     pkt[PeregrineHdr].five_t_radius,
                     pkt[PeregrineHdr].five_t_sum_res_prod_cov,
                     pkt[PeregrineHdr].five_t_pcc]]
        pkt_header = [pkt[Ether].src, pkt[IP].src, pkt[IP].dst, pkt[IP].proto]
        if UDP in pkt:
            pkt_header.append(str(pkt[UDP].sport))
            pkt_header.append(str(pkt[UDP].dport))
        elif TCP in pkt:
            pkt_header.append(str(pkt[TCP].sport))
            pkt_header.append(str(pkt[TCP].dport))
        else:
            # If not UDP/TCP, the sport and dport values will be 0.
            pkt_header.append('0')
            pkt_header.append('0')
        cur_stats.insert(0, pkt_header)


def pkt_pipeline(cur_eg_veth, pcap_path, trace_labels_path, sampling_rate,
                 exec_phase, fm_grace, ad_grace, max_ae, feature_map,
                 ensemble_layer, output_layer, train_stats, attack, exact_stats,
                 train_exact_ratio):
    global cur_stats
    global threshold
    global rmse_list
    global pkt_header
    global pkt_cnt_global
    train_skip = False

    # Statistics are calculated with/without data plane approximations according
    # to the exact_stats flag.
    if exact_stats:
        from stats_calc_exact import StatsCalc
    else:
        from stats_calc import StatsCalc

    # Read the csv containing the ground truth labels.
    trace_labels = pd.read_csv(trace_labels_path, header=None)

    if exec_phase == 'dp':
        split_layers(Ether, IP, type=0x0800)
        bind_layers(Ether, PeregrineHdr, type=0x0800)
        bind_layers(PeregrineHdr, IP)

    if feature_map is not None and \
            ensemble_layer is not None and \
            output_layer is not None and \
            train_stats is not None:
        train_skip = True

    # Build Peregrine.
    peregrine = Peregrine(max_ae, fm_grace, ad_grace, learning_rate, hidden_ratio, lambdas,
                          exec_phase, feature_map, ensemble_layer, output_layer, train_stats,
                          attack, train_skip, train_exact_ratio)

    # Initialize the feature extraction and calculation of statistics class.
    peregrine_stats = StatsCalc(pcap_path, sampling_rate, fm_grace+ad_grace, train_skip)

    trace_size = peregrine_stats.trace_size()

    # Process the trace, packet by packet.
    while True:
        cur_stats = 0

        if not train_skip:
            if len(rmse_list) % 1000 == 0 and len(rmse_list) < fm_grace + ad_grace:
                print('Processed packets: ', len(rmse_list))
            elif pkt_cnt_global % 1000 == 0 and len(rmse_list) >= fm_grace + ad_grace:
                print('Processed packets: ', fm_grace + ad_grace + pkt_cnt_global)
        else:
            if pkt_cnt_global % 1000 == 0:
                print('Processed packets: ', fm_grace + ad_grace + pkt_cnt_global)

        # Training phase.
        if len(rmse_list) < (train_exact_ratio * (fm_grace + ad_grace)) and not train_skip:
            peregrine_stats.feature_extract()
            cur_stats = peregrine_stats.process_exact('training')
        elif len(rmse_list) < fm_grace + ad_grace and not train_skip:
            peregrine_stats.feature_extract()
            cur_stats = peregrine_stats.process('training')

        # Execution phase.
        else:
            # Execution:  data plane
            if exec_phase == 'dp':
                # Callback function to retrieve the packet's custom header.
                sniff(iface=cur_eg_veth, count=1, prn=pkt_callback, timeout=9999999)

            # Execution:  control plane
            else:
                pkt_cnt_global += 1
                peregrine_stats.feature_extract()
                cur_stats = peregrine_stats.process('execution')

        # If any statistics were obtained, send them to the ML pipeline.
        if cur_stats != 0:
            # Execution phase: only proceed according to the sampling rate.
            # if len(rmse_list) >= fm_grace + ad_grace and pkt_cnt_global % sampling_rate != 0:
            if pkt_cnt_global % sampling_rate != 0:
                # Break when we reach the end of the trace file.
                if fm_grace + ad_grace + pkt_cnt_global == trace_size:
                    break
                else:
                    continue

            # Flatten the statistics' list of lists.
            cur_stats = list(itertools.chain(*cur_stats))
            cur_stats_global.append(cur_stats)
            # Call function with the content of kitsune's main (before the eval/csv part).
            rmse = peregrine.proc_next_packet(cur_stats)
            rmse_list.append(rmse)
            try:
                peregrine_eval.append([cur_stats[0], cur_stats[1], cur_stats[2],
                                       cur_stats[3], cur_stats[4], cur_stats[5],
                                       rmse,
                                       trace_labels.iat[fm_grace + ad_grace + pkt_cnt_global - 1, 0]])
            except IndexError:
                print(trace_labels.shape[0])
                print(pkt_cnt_global)
                print(fm_grace + ad_grace + pkt_cnt_global - 1)

            # At the end of the training phase, store the highest rmse value as the threshold.
            # Also, save the stored stat values.
            if not train_skip and len(rmse_list) == fm_grace + ad_grace:
                threshold = max(rmse_list, key=float)
                peregrine.save_train_stats()
                print('Starting execution phase...')

            # Break when we reach the end of the trace file.
            elif fm_grace + ad_grace + pkt_cnt_global == trace_size:
                peregrine.save_exec_stats()
                break
        else:
            print('TIMEOUT.')
            break

    return [rmse_list, cur_stats_global, peregrine_eval, threshold, train_skip]
