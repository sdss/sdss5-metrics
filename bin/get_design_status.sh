#!/bin/bash

source /home/users/jbochanski/.bashrc
module load sdssdb/main
python /home/users/jbochanski/get_design_status.py
python /home/users/jbochanski/run_metrics_apo.py
cp -r /home/users/jbochanski/metrics_plots/ /home/sdss5/tmp/

