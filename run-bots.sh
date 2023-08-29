source ./venv/bin/activate

python bot.py 0546554837 AmazingNight123! &
pid1=$!

python bot.py 0546602892 AmazingNight123! &
pid2=$!

python bot.py 0546603846 AmazingNight123! &
pid3=$!

python bot.py 0546607458 AmazingNight123! &
pid4=$!

python bot.py 0546605274 AmazingNight123! &
pid5=$!

stop_jobs() {
    echo "Stopping all jobs..."
    kill $pid1 $pid2 $pid3 $pid4 $pid5
    echo "All jobs stopped"
    exit 0
}

trap 'stop_jobs' SIGINT

wait

echo "All bots finished"
