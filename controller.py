#!/usr/bin/env python3

import os
import sys
import signal
import logging
import argparse
import time
import yaml
import pipeline
from pipeline import pkt_pipeline
from eval_metrics import eval_metrics

logger = None

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="peregrine-py")
    argparser.add_argument('-p', '--plugin', type=str, help='Plugin')
    argparser.add_argument('-c', '--conf', type=str, help='Config path')
    args = argparser.parse_args()

    with open(args.conf, "r") as yaml_conf:
        conf = yaml.load(yaml_conf, Loader=yaml.FullLoader)

    # configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(args.plugin)

    start = time.time()

    # Call function to run the packet processing pipeline.
    # Encompasses both training phase + execution phase.
    pipeline_out = pkt_pipeline(
        conf['trace'], conf['labels'], conf['sampling'], conf['fm_grace'], conf['ad_grace'],
        conf['max_ae'], conf['fm_model'], conf['el_model'], conf['ol_model'], conf['train_stats'],
        conf['attack'], conf['exact_stats'], conf['train_exact_ratio'])

    stop = time.time()
    total_time = stop - start

    print('Complete. Time elapsed: ', total_time)
    print('Threshold: ', pipeline.threshold)

    # Call function to perform eval/csv, also based on kitsune's main.
    # pipeline_out: rmse_list [0], cur_stats_global [1], peregrine_eval[2],
    # threshold [3], train_skip flag [4].
    eval_metrics(
        pipeline_out[0], pipeline_out[1], pipeline_out[2], pipeline_out[3], pipeline_out[4],
        conf['fm_grace'], conf['ad_grace'], conf['attack'], conf['sampling'], conf['max_ae'],
        conf['train_exact_ratio'], total_time)

    # exit (bug workaround)
    logger.info("Exiting!")

    # flush logs, stdout, stderr
    logging.shutdown()
    sys.stdout.flush()
    sys.stderr.flush()

    # exit (bug workaround)
    os.kill(os.getpid(), signal.SIGTERM)
