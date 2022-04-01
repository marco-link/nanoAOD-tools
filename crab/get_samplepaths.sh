#!/bin/bash

dasgoclient --query="dataset=/*/mlink*ChargeReco*v6*/USER instance=prod/phys03" | tee samples.txt
