# ./run_servers.sh 3

num_server=$1

echo "Starting $num_server servers."
for i in $(seq 1 $num_server)
do
    echo $i
    python server.py --log=INFO &
done
