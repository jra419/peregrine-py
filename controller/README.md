# Peregrine controller

## Run Tofino model

`--int-port-loop 2`: 2 = 0b10, make pipe 1 (second bit) be an internal looping pipe, and pipe 0 a normal pipe.

```
$ ./run_tofino_model.sh -p peregrine --int-port-loop 2 -f ~/confs/ports.json -c ~/confs/BFN-T10-032D-model.conf
```
