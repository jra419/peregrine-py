#!/usr/bin/env python3

import sys
import logging
import argparse
import time
import yaml
from eval_metrics import eval_kitnet, eval_enidrift, eval_whisper
from pipeline_kitnet import PipelineKitNET
from pipeline_enidrift import PipelineENIDrift
from pipeline_whisper import PipelineWhisper

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
            conf['trace'], conf['labels'], conf['sampling'], conf['exec_sampl_offset'],
            conf['fm_grace'], conf['ad_grace'], conf['max_ae'], conf['fm_model'],
            conf['el_model'], conf['ol_model'], conf['train_stats'], conf['attack'],
            conf['train_exact_ratio'], conf['save_stats_global'])
    elif args.plugin == 'enidrift':
        pipeline = PipelineENIDrift(
            conf['trace'], conf['labels'], conf['sampling'], conf['attack'], conf['hypr'],
            conf['delta'], conf['incr'], conf['release_speed'], conf['save_stats_global'])
    elif args.plugin == 'whisper':
        pipeline = PipelineWhisper(conf['trace'], conf['labels'], conf['sampling'],
                                   conf['train_size'], conf['dst_mac'])

    pipeline.process()

    stop = time.time()
    total_time = stop - start

    print('Complete. Time elapsed: ', total_time)

    # Call function to perform eval/csv.
    if args.plugin == 'kitnet':
        print('Threshold: ', pipeline.threshold)
        eval_kitnet(
            pipeline.rmse_list, pipeline.stats_global, pipeline.peregrine_eval,
            pipeline.threshold, pipeline.train_skip, conf['fm_grace'],
            conf['ad_grace'], conf['attack'], conf['sampling'], conf['exec_sampl_offset'],
            conf['max_ae'], conf['train_exact_ratio'], conf['save_stats_global'], total_time)
    elif args.plugin == 'enidrift':
        eval_enidrift(pipeline.prediction, pipeline.stats_global, pipeline.peregrine_eval,
                      conf['attack'], conf['sampling'],conf['release_speed'],
                      conf['save_stats_global'], total_time)
    elif args.plugin == 'whisper':
        eval_whisper(pipeline.stats_global, conf['attack'], conf['sampling'], total_time)

    # exit (bug workaround)
    logger.info("Exiting!")

    # flush logs, stdout, stderr
    logging.shutdown()
    sys.stdout.flush()
    sys.stderr.flush()

    # exit (bug workaround)
    # os.kill(os.getpid(), signal.SIGTERM)
