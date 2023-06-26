#!/usr/bin/env python3

import os
import sys
import signal
import logging
import argparse
import time
import yaml
from eval_metrics import eval_kitnet
from pipeline_kitnet import PipelineKitNET

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
    if args.plugin == 'kitnet':
        pipeline = PipelineKitNET(
            conf['trace'], conf['labels'], conf['sampling'], conf['fm_grace'], conf['ad_grace'],
            conf['max_ae'], conf['fm_model'], conf['el_model'], conf['ol_model'],
            conf['train_stats'], conf['attack'], conf['train_exact_ratio'])

        pipeline.process()

    stop = time.time()
    total_time = stop - start

    print('Complete. Time elapsed: ', total_time)
    print('Threshold: ', pipeline.threshold)

    # Call function to perform eval/csv.
    if args.plugin == 'kitnet':
        eval_kitnet(
            pipeline.rmse_list, pipeline.cur_stats_global, pipeline.peregrine_eval,
            pipeline.threshold, pipeline.train_skip, conf['fm_grace'], conf['ad_grace'],
            conf['attack'], conf['sampling'], conf['max_ae'], conf['train_exact_ratio'], total_time)

    # exit (bug workaround)
    logger.info("Exiting!")

    # flush logs, stdout, stderr
    logging.shutdown()
    sys.stdout.flush()
    sys.stderr.flush()

    # exit (bug workaround)
    os.kill(os.getpid(), signal.SIGTERM)
