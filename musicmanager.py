import os
import subprocess
import slugify
import logging
import json
import argparse
import sys
from PIL import Image


class Playlist:
    savePathRoot = None

    def __init__(self, link, downloadWholePlaylist=True, name=None):
        if not self.savePathRoot:
            raise Exception('\'savePathRoot\' must be defined.')

        self.name = name
        self.link = link
        self.downloadWholePlaylist = downloadWholePlaylist
        if name:
            self.savePath = os.path.join(self.savePathRoot, name)
        else:
            self.savePath = self.savePathRoot

        if self.name:
            logName = f'.{slugify.slugify(self.name)}-downloaded-archive.txt'  # todo check
            self.downloadArchivePath = os.path.join(self.savePath, logName)
        else:
            self.downloadArchivePath = os.path.join(self.savePath, '.downloaded-archive.txt')

        if not os.path.exists(self.savePath):
            os.makedirs(self.savePath)

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
            self.downloadArchivePath,
            '--yes-playlist' if self.downloadWholePlaylist else '--no-playlist',
            '--no-post-overwrites',
            '--embed-thumbnail',
            '--output',
            os.path.join(self.savePath, '+%(title)s %(id)s.%(ext)s'),
            self.link
        ])

        logger.info(f'Download to {os.path.abspath(self.savePath)} finished.')

    def fixAlbumArt(self):
        for fileName in os.listdir(self.savePath):
            if fileName.startswith('+') and fileName.endswith('.mp3'):
                # Extract the image from mp3 file
                subprocess.run([
                    'ffmpeg',
                    '-i',
                    os.path.join(self.savePath, fileName),
                    '-an',
                    '-c:v',
                    'copy',
                    os.path.join(self.savePath, 'tmp-art-uncropped.jpg')
                ])

                # Crop & save the image
                im = Image.open(os.path.join(self.savePath, 'tmp-art-uncropped.jpg'))
                width, height = im.size

                left = int((width - height) / 2)
                upper = 0
                right = left + height
                lower = height

                im = im.crop((left, upper, right, lower))
                im.save(os.path.join(self.savePath, 'tmp-art-cropped.jpg'))

                # Embed the image
                subprocess.run([
                    'ffmpeg',
                    '-i',
                    os.path.join(self.savePath, fileName),
                    '-i',
                    os.path.join(self.savePath, 'tmp-art-cropped.jpg'),
                    '-map',
                    '0:0',
                    '-map',
                    '1:0',
                    '-c',
                    'copy',
                    '-id3v2_version',
                    '3',
                    '-metadata:s:v',
                    'title=Album cover',  # vzel sm ""
                    '-metadata:s:v',
                    'comment=Cover (front)',  # vzel sm ""
                    os.path.join(self.savePath, fileName[1:])
                ])

                # Clean up
                os.remove(os.path.join(self.savePath, 'tmp-art-uncropped.jpg'))
                os.remove(os.path.join(self.savePath, 'tmp-art-cropped.jpg'))
                os.remove(os.path.join(self.savePath, fileName))

                logger.info(f'Fixed album art in {os.path.abspath(self.savePath)}')


if __name__ == '__main__':
    # LOGGING SETUP
    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler('logger.log')
    fileHandler.setLevel(logging.INFO)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileHandler.setFormatter(formatter)
    consoleHandler.setFormatter(formatter)

    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)

    # ARGUMENT PARSING. for configurations made at command line, ignoring config file
    argParser = argparse.ArgumentParser(
        description='Download YouTube Music and other content hassle-free.',
        epilog='Example: python3 musicmanager.py ...neki...'  # todo
    )

    actions = (
        'quick',
        'q',
        'playlist',
        'pl',
        'song',
        'so',
    ) # shorter ones are aliases
    argParser.add_argument(
        'action',
        nargs='?',
        default=None,
        choices=actions,
        help='Choose one of: quick or q - download all songs from playlist defined under \'quickDownloadPlaylistLink\', playlist or pl - download all songs from provided URL, song or so - download a single song from provided URL.'
    )  # todo maybe delete nargs. but hey it works
    argParser.add_argument(
        'url',
        nargs='?',
        type=str,
        help='Content URL.'
    )  # todo maybe delete nargs. but hey it works

    args = argParser.parse_args()

    with open('config.json', 'r') as f:
        config = json.load(f)

    # download by config file, default functionality
    if not args.action:
        # main playlists
        Playlist.savePathRoot = config['savePathRoot']

        for playlist in config['playlist']:
            mainPlaylist = Playlist(playlist['link'], downloadWholePlaylist=True, name=playlist['name'])
            mainPlaylist.download()
            mainPlaylist.fixAlbumArt()

    # download quick download playlist
    elif args.action == 'quick' or args.action == 'q':
        Playlist.savePathRoot = './'
        quickDownload = Playlist(config['quickDownloadPlaylistLink'], downloadWholePlaylist=True)
        quickDownload.download()
        quickDownload.fixAlbumArt()

    elif args.url:
        # download custom playlist
        if args.action == 'playlist' or args.action == 'pl':
            Playlist.savePathRoot = './'
            quickDownload = Playlist(args.url, downloadWholePlaylist=True)
            quickDownload.download()
            quickDownload.fixAlbumArt()

        # download custom song
        elif args.action == 'song' or args.action == 'so':
            Playlist.savePathRoot = './'
            quickDownload = Playlist(args.url, downloadWholePlaylist=False)
            quickDownload.download()
            quickDownload.fixAlbumArt()

    elif not args.url:
        raise Exception('URL not provided.')

    else:
        raise Exception('Malformed command/args.')
