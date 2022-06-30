#!/bin/bash

dasgoclient --query="dataset=/*/mlink*ChargeReco*2022-06-22_v10*/USER instance=prod/phys03" | tee samples.txt
