# source ./venv/bin/activate

# python3 bot.py 0546554837 AmazingNight123! http://xdjtexfm:89sugm26m8a5@2.56.119.93:5074 &
python3 bot.py 0546602459 AmazingNight123! &
pid1=$!

# python3 bot.py 0546602892 AmazingNight123! http://xdjtexfm:89sugm26m8a5@185.199.229.156:7492 &
python3 bot.py 0546605107 AmazingNight123! &
pid2=$!

# python3 bot.py 0546603846 AmazingNight123! http://xdjtexfm:89sugm26m8a5@185.199.228.220:7300 &
python3 bot.py 0546603846 AmazingNight123! &
pid3=$!

# python3 bot.py 0546607458 AmazingNight123! http://xdjtexfm:89sugm26m8a5@185.199.231.45:8382 &
# python3 bot.py 0546607458 AmazingNight123! &

# pid4=$!

# python3 bot.py 0546605274 AmazingNight123! http://xdjtexfm:89sugm26m8a5@188.74.210.207:6286 &
python3 bot.py 0546605274 AmazingNight123!  &
pid5=$!

stop_jobs() {
    echo "Stopping all jobs..."
    kill $pid1 $pid2 $pid3 $pid4 $pid5
    echo "All jobs stopped"
    exit 0
}

trap 'stop_jobs' INT TERM

wait

echo "All bots finished"
