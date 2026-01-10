  #!/bin/bash
  while true; do
      sleep 60
      if ! pgrep -f "flight_logger_enhanced.py" > /dev/null; then
          echo "$(date): Restarting flight logger..." >> ~/adsb-tracker/logs/watchdog.log
          cd ~/adsb-tracker
          nohup python3 flight_logger_enhanced.py > logs/flight_logger.log 2>&1 &
      fi
  done
