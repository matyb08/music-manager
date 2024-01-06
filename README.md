# setup

## virtualenv
_used python 3.10_
```shell
python3 -m venv .venv
.venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## host

- Add project folder to PATH
- install ffmpeg and yt-dlp
  ```shell
  sudo apt install -y ffmpeg
  sudo python3 -m pip install yt-dlp
  ```
- alias to `mm` 😉