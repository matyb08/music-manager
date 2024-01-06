import os
import pathlib
import subprocess
import slugify
import logging
import json
import argparse
from PIL import Image

PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()


class Playlist:
    def __init__(self, link, save_path_root='./', download_whole_playlist=True, name=None):
        self.save_path_root = save_path_root
        self.name = name
        self.link = link
        self.download_whole_playlist = download_whole_playlist
        if name:
            self.save_path = os.path.join(self.save_path_root, name)
        else:
            self.save_path = self.save_path_root

        if self.name:
            self.download_archive_path = os.path.join(
                self.save_path,
                f'.{slugify.slugify(self.name)}-downloaded-archive.txt'
            )
        else:
            self.download_archive_path = os.path.join(self.save_path, '.downloaded-archive.txt')

        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def download(self):
        subprocess.run([
            'yt-dlp',
            '--extract-audio',
            '--audio-quality',
            '0',
            '--audio-format',
            'mp3',
            '--ignore-errors',
            '--add-metadata',
            '--download-archive',
            self.download_archive_path,
            '--yes-playlist' if self.download_whole_playlist else '--no-playlist',
            '--no-post-overwrites',
            '--embed-thumbnail',
            '--output',
            os.path.join(self.save_path, '+%(title)s %(id)s.%(ext)s'),
            self.link
        ])

        musicmanager_logger.info(f'Download to {os.path.abspath(self.save_path)} finished.')

    def fix_album_art(self):
        for file_name in os.listdir(self.save_path):
            if file_name.startswith('+') and file_name.endswith('.mp3'):
                # Extract the image from mp3 file
                subprocess.run([
                    'ffmpeg',
                    '-i',
                    os.path.join(self.save_path, file_name),
                    '-an',
                    '-c:v',
                    'copy',
                    os.path.join(self.save_path, 'tmp-art-uncropped.jpg')
                ])

                # Crop & save the image
                im = Image.open(os.path.join(self.save_path, 'tmp-art-uncropped.jpg'))
                width, height = im.size

                left = int((width - height) / 2)
                upper = 0
                right = left + height
                lower = height

                im = im.crop((left, upper, right, lower))
                im.save(os.path.join(self.save_path, 'tmp-art-cropped.jpg'))

                # Embed the image
                subprocess.run([
                    'ffmpeg',
                    '-i',
                    os.path.join(self.save_path, file_name),
                    '-i',
                    os.path.join(self.save_path, 'tmp-art-cropped.jpg'),
                    '-map',
                    '0:0',
                    '-map',
                    '1:0',
                    '-c',
                    'copy',
                    '-id3v2_version',
                    '3',
                    '-metadata:s:v',
                    'title=Album cover',
                    '-metadata:s:v',
                    'comment=Cover (front)',
                    os.path.join(self.save_path, file_name[1:])
                ])

                # Clean up
                os.remove(os.path.join(self.save_path, 'tmp-art-uncropped.jpg'))
                os.remove(os.path.join(self.save_path, 'tmp-art-cropped.jpg'))
                os.remove(os.path.join(self.save_path, file_name))

                musicmanager_logger.info(f'Fixed album art in {os.path.abspath(self.save_path)}')


def setup_logger():
    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(os.path.join(PROJECT_ROOT, 'logger.log'))
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_config():
    with open(os.path.join(PROJECT_ROOT, 'config.json'), 'r') as f:
        return json.load(f)


def get_args():
    arg_parser = argparse.ArgumentParser(
        description='Download YouTube Music and other content hassle-free.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''
Examples:
python musicmanager.py
python musicmanager.py quick
python musicmanager.py so 'https://music.youtube.com/watch?v=0hnwIedsoNI'
 
'''
    )

    actions = (
        'quick', 'q',
        'playlist', 'pl',
        'song', 'so'
    )
    arg_parser.add_argument(
        'action',
        default=None,
        nargs='?',
        choices=actions,
        help='''
Choose one of:
- quick or q - download all songs from playlist defined under \'quickDownloadPlaylistLink\',
- playlist or pl - download all songs from provided URL,
- song or so - download a single song from provided URL.
 
'''
    )

    arg_parser.add_argument(
        'url',
        default=None,
        nargs='?',
        help='URL of the playlist or song to download.'
    )

    return arg_parser.parse_args()


if __name__ == '__main__':
    musicmanager_logger = setup_logger()
    args = get_args()
    config = get_config()

    # download by config file, default functionality
    if not args.action:
        for playlist in config['playlist']:
            config_download = Playlist(
                playlist['link'],
                save_path_root=config['savePathRoot'],
                download_whole_playlist=True, name=playlist['name']
            )
            config_download.download()
            config_download.fix_album_art()

    # download quick download playlist
    elif args.action == 'quick' or args.action == 'q':
        quick_playlist_download = Playlist(config['quickDownloadPlaylistLink'], download_whole_playlist=True)
        quick_playlist_download.download()
        quick_playlist_download.fix_album_art()

    elif args.url:
        # download custom playlist
        if args.action == 'playlist' or args.action == 'pl':
            custom_playlist_download = Playlist(args.url, download_whole_playlist=True)
            custom_playlist_download.download()
            custom_playlist_download.fix_album_art()

        # download custom song
        elif args.action == 'song' or args.action == 'so':
            custom_song_download = Playlist(args.url, download_whole_playlist=False)
            custom_song_download.download()
            custom_song_download.fix_album_art()

    elif not args.url:
        musicmanager_logger.error('URL must be provided.')
    else:
        musicmanager_logger.error('Malformed command/args.')
