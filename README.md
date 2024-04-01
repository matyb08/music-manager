# help

run:

```shell
python musicmanager.py --help
```

# setup

## virtualenv

_used python 3.10_

```shell
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## host

- Add project folder to PATH
- install ffmpeg and yt-dlp globally:
  ```shell
  sudo apt install -y ffmpeg
  sudo python3 -m pip install yt-dlp
  ```
- alias to `mm` 😉
