export REDIS_URL="redis://:redis@pub-redis-14008.us-east-1-4.2.ec2.garantiadata.com:14008"
redis-cli -h pub-redis-14008.us-east-1-4.2.ec2.garantiadata.com -p 14008 -a redis
 curl -s -d name=Chris2 -d email=cwilkes@ladro.com http://127.0.0.1:5000/
 curl -s -d name=Chris -d email=cwilkes@gmail.com http://127.0.0.1:5000/
 curl -s http://127.0.0.1:5000/
 curl -s http://127.0.0.1:5000/2
