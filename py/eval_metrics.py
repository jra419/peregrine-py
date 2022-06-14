import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from matplotlib import colors
from matplotlib import pyplot as plt
from sklearn import metrics

ts_datetime = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')[:-3]


def eval_metrics(rmse_list, cur_stats_global, peregrine_eval, threshold, fm_grace, ad_grace,
                 exec_phase, attack, sampling):
    outdir = str(Path(__file__).parents[0]) + '/eval/' + exec_phase
    if not os.path.exists(str(Path(__file__).parents[0]) + '/eval'):
        os.mkdir(outdir)
    outpath_peregrine = os.path.join(outdir, attack + '-' + str(sampling) + '-rmse-' + ts_datetime + '.csv')
    outpath_cur_stats_global = os.path.join(outdir, attack + '-' + str(sampling) + '-stats-' + ts_datetime + '.csv')

    # Collect the global stats and save to a csv.
    df_cur_stats_global = pd.DataFrame(cur_stats_global)
    df_cur_stats_global.to_csv(outpath_cur_stats_global, index=None)

    # Collect the processed packets' RMSE, label, and save to a csv.
    df_peregrine = pd.DataFrame(peregrine_eval,
                                columns=['ip_src', 'ip_dst', 'ip_type', 'src_proto', 'dst_proto', 'rmse', 'label'])
    df_peregrine.to_csv(outpath_peregrine, index=None)

    # Cut all training rows.
    df_peregrine_cut = df_peregrine.drop(df_peregrine.index[range(fm_grace + ad_grace)])

    # Sort by RMSE.
    df_peregrine_cut.sort_values(by='rmse', ascending=False, inplace=True)

    # Split by threshold.
    peregrine_benign = df_peregrine_cut[df_peregrine_cut.rmse < threshold]
    print(peregrine_benign.shape[0])
    peregrine_alert = df_peregrine_cut[df_peregrine_cut.rmse >= threshold]
    print(peregrine_alert.shape[0])

    # Calculate statistics.
    TP = peregrine_alert[peregrine_alert.label == 1].shape[0]
    FP = peregrine_alert[peregrine_alert.label == 0].shape[0]
    TN = peregrine_benign[peregrine_benign.label == 0].shape[0]
    FN = peregrine_benign[peregrine_benign.label == 1].shape[0]

    try:
        TPR = TP / (TP + FN)
    except ZeroDivisionError:
        TPR = 0

    try:
        TNR = TN / (TN + FP)
    except ZeroDivisionError:
        TNR = 0

    try:
        FPR = FP / (FP + TN)
    except ZeroDivisionError:
        FPR = 0

    try:
        FNR = FN / (FN + TP)
    except ZeroDivisionError:
        FNR = 0

    try:
        accuracy = (TP + TN) / (TP + FP + FN + TN)
    except ZeroDivisionError:
        accuracy = 0

    try:
        precision = TP / (TP + FP)
    except ZeroDivisionError:
        precision = 0

    try:
        recall = TP / (TP + FN)
    except ZeroDivisionError:
        recall = 0

    try:
        f1_score = 2 * (recall * precision) / (recall + precision)
    except ZeroDivisionError:
        f1_score = 0

    roc_curve_fpr, roc_curve_tpr, roc_curve_thres = metrics.roc_curve(df_peregrine.label, df_peregrine.rmse)
    roc_curve_fnr = 1 - roc_curve_tpr

    auc = metrics.roc_auc_score(df_peregrine.label, df_peregrine.rmse)
    eer = roc_curve_fpr[np.nanargmin(np.absolute((roc_curve_fnr - roc_curve_fpr)))]
    eer_sanity = roc_curve_fnr[np.nanargmin(np.absolute((roc_curve_fnr - roc_curve_fpr)))]

    print('TP: ' + str(TP))
    print('TN: ' + str(TN))
    print('FP: ' + str(FP))
    print('FN: ' + str(FN))
    print('TPR: ' + str(TPR))
    print('TNR: ' + str(TNR))
    print('FPR: ' + str(FPR))
    print('FNR: ' + str(FNR))
    print('Accuracy: ' + str(accuracy))
    print('precision: ' + str(precision))
    print('Recall: ' + str(recall))
    print('F1 Score: ' + str(f1_score))
    print('AuC: ' + str(auc))
    print('EER: ' + str(eer))
    print('EER sanity: ' + str(eer_sanity))

    # Write the eval to a txt.
    f = open('eval/' + exec_phase + '/' + attack + '-' + str(sampling) + '-metrics-' + ts_datetime + '.txt', 'a+')
    f.write('Threshold: ' + str(threshold) + '\n')
    f.write('TP: ' + str(TP) + '\n')
    f.write('TN: ' + str(TN) + '\n')
    f.write('FP: ' + str(FP) + '\n')
    f.write('FN: ' + str(FN) + '\n')
    f.write('TPR: ' + str(TPR) + '\n')
    f.write('TNR: ' + str(TNR) + '\n')
    f.write('FPR: ' + str(FPR) + '\n')
    f.write('FNR: ' + str(FNR) + '\n')
    f.write('Accuracy: ' + str(accuracy) + '\n')
    f.write('Precision: ' + str(precision) + '\n')
    f.write('Recall: ' + str(recall) + '\n')
    f.write('F1 Score: ' + str(f1_score) + '\n')
    f.write('AuC: ' + str(auc) + '\n')
    f.write('EER: ' + str(eer) + '\n')
    f.write('EER sanity: ' + str(eer_sanity) + '\n')
    f.close()

    # Plot the RMSE anomaly scores.
    print("Plotting results")
    plt.figure(figsize=(10, 5))
    cmap = colors.ListedColormap(['green', 'red'])
    bounds = [0, threshold, max(rmse_list[fm_grace+ad_grace+1:])]
    norm = colors.BoundaryNorm(bounds, cmap.N)
    cmap.set_over('red')
    cmap.set_under('green')
    plt.scatter(range(fm_grace+ad_grace+1, len(rmse_list)), rmse_list[fm_grace+ad_grace+1:],
                s=0.1, c=rmse_list[fm_grace+ad_grace+1:], cmap=cmap, norm=norm)
    plt.yscale("log")
    plt.title("Anomaly Scores from Peregrine's Execution Phase")
    plt.ylabel("RMSE (log scaled)")
    plt.xlabel("Packets")
    plt.hlines(xmin=0, xmax=len(rmse_list), y=threshold, colors='blue', label=threshold)
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3))
    plt.subplots_adjust(bottom=0.25)
    plt.colorbar()
    plt.savefig('eval/' + exec_phase + '/' + attack + '-' + str(sampling) + '-' + ts_datetime + '.png')
