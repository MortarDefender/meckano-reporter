#!/bin/bash

sudo apt update
sudo apt install python3-pip -y
pip3 install argparse
pip3 install -U selenium
sudo cp -r utils/geckodriver /usr/local/bin

current_dir=$(pwd)

sed -i "s#<script_directory>#$current_dir#" Meckano-Reporter.desktop
sudo chmod 777 Meckano-Reporter.desktop
sudo cp -r Meckano-Reporter.desktop /usr/share/applications/Meckano-Reporter.desktop

sed -i "s#<script_directory>#$current_dir#" report_last_week.sh report_month.sh report_today.sh
sudo chmod +x report_month.sh
sudo chmod +x report_last_week.sh
sudo chmod +x report_today.sh

sed -i "s#<script_directory>#$current_dir#" install_script.sh
