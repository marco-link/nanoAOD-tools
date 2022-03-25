#!/bin/bash

dasgoclient --query="dataset=/*/mlink*ChargeReco*v5*/USER instance=prod/phys03" | tee samples.txt
