
ps -ef | grep doobot_main | grep python | awk '{print $2}' | xargs kill -9

