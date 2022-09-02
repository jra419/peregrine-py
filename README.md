# Peregrine

Peregrine is an anomaly-based detection system that leverages the programmable data plane to execute a subset of the overall intrusion detection pipeline. Specifically, it performs traffic feature extraction and the calculation of statistics entirely on the data plane switches. The subsequent machine learning-based classification is performed at the control plane level.

Each execution is split into two phases: training and execution. The first phase, which runs on the control plane, is used to train the ML model with benign traffic.

For testing purposes, the data plane processing can be simulated in the control plane through an execution flag.

## Compilation

The following build script is available in `ica_tools.tgz`, available in the lab gdrive folder.

```
$ ~/tools/p4_build.sh ~/peregrine/p4/peregrine.p4
```

## Example execution

Tested on the Tofino SDE 9.7.0.

### Setup virtual interfaces.

```
$ $SDE/install/bin/veth_setup.sh
```

### Start the Tofino model.

```
$ ./run_tofino_model.sh --arch tofino -p ~/peregrine/p4/peregrine.p4 -c ~/peregrine/p4/multipipe_custom_bfrt.conf --int-port-loop 0xa -q
```

### Start Switchd.

```
$ ./run_switchd.sh -p peregrine
```

### Start the controller.

```
$ python3 ~/peregrine/py/controller.py --pcap $TEST_PCAP --labels $TRACE_LABELS_FILE --sampling $SAMPLING_RATE --execution $EXEC_MODE --attack $ATTACK_NAME
```

`$TEST_PCAP`: path to the desired trace file.

`$TRACE_LABELS_FILE`: path to the trace file labels.

`$SAMPLING_RATE`: the desired sampling rate for the execution phase. Integer value (e.g., 8 means a sampling rate of 1/8).

`$EXEC_MODE`: define if the execution phase runs on the control/data plane (possible values: dp, cp).

`$ATTACK_NAME`: attack(s) present in the trace file, used for generating the output files (e.g., dos-goldeneye).

### Trace file replay (execution phase).

As an example, the following command uses `tcpreplay` to replay the trace file to `veth0`:

```
$ tcpreplay -i veth0 $TEST_PCAP_EXECUTION
```

If a specific trace replay results in an error due a packet being larger than the defined MTU size, `tcpreplay-edit` can be used to truncate all trace packets (with some performance loss):

```
$ tcpreplay-edit --mtu-trunc -i veth0 $TEST_PCAP_EXECUTION
```
