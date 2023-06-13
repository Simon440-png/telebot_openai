#!/bin/bash
echo "files are copied..."
#copy all files
cp *.service /etc/systemd/system
cp -r OpenAI /
echo "Launch processes..."
#launch system processes and include in autoload 
systemctl start telegram-bot && systemctl enable telegram-bot
systemctl start panel-bot && systemctl enable panel-bot
systemctl start main-beta && systemctl enable main-beta
echo "All ready!"
