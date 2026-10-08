import requests

res = requests.get("http://127.0.0.1:5000/joke")

if res.status_code != 200:
    exit
else:
    print('works !!!!!')
