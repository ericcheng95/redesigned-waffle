"""Code mostly taken from https://github.com/ndrplz/google-drive-downloader
Use to download replays from Google Drive.
You could also use the official Google Drive API, but that would require
that you have an API key, so that's impractical.
USAGE: Called in download_replays.py, which downloads replays from the replay
vault in an instant.
"""
from __future__ import print_function
import requests
import zipfile
import warnings
from sys import stdout
from os import makedirs
import os
from os.path import dirname
from os.path import exists




class GoogleDriveDownloader:
  """
  Minimal class to download shared files from Google Drive.
  """

  CHUNK_SIZE = 32768
  DOWNLOAD_URL = 'https://docs.google.com/uc?export=download'

  @staticmethod
  def download_file_from_google_drive(file_id, dest_path, new_file_name,
                                      overwrite=False, unzip=False,
                                      showsize=False):
    """
    Downloads a shared file from google drive into a given folder.
    Optionally unzips it.
    Parameters
    ----------
    file_id: str
        the file identifier.
        You can obtain it from the sharable link.
    dest_path: str
        the destination where to save the downloaded file.
        Must be a path (for example: './downloaded_file.txt')
    new_file_name: str
        File name prefix to append to the extracted file. Specify to
        ensure that names are unique, so no files are overwritten.
    overwrite: bool
        optional, if True forces re-download and overwrite.
    unzip: bool
        optional, if True unzips a file.
        If the file is not a zip file, ignores it.
    showsize: bool
        optional, if True print the current download size.
    Returns
    -------
    None
    """

    destination_directory = dirname(dest_path)
    if not exists(destination_directory):
      makedirs(destination_directory)

    if not exists(dest_path) or overwrite:

      session = requests.Session()

      print('Downloading {} into {}... '.format(
          file_id, dest_path), end='')
      stdout.flush()

      response = session.get(GoogleDriveDownloader.DOWNLOAD_URL, params={
                             'id': file_id}, stream=True)

      token = GoogleDriveDownloader._get_confirm_token(response)
      if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(
            GoogleDriveDownloader.DOWNLOAD_URL, params=params, stream=True)

      if showsize:
        print()  # Skip to the next line

      current_download_size = [0]
      GoogleDriveDownloader._save_response_content(
          response, dest_path, showsize, current_download_size)
      print('Done.')

      if unzip:
        try:
          print('Unzipping...', end='')
          stdout.flush()
          with zipfile.ZipFile(dest_path, 'r') as z:
            for zip_info in z.infolist():
              # Ignore directory.
              if zip_info.filename[-1] == '/':
                continue
              zip_info.filename = new_file_name + \
                  os.path.basename(zip_info.filename)
              z.extract(zip_info, destination_directory)
          print('Done.')
        except zipfile.BadZipfile:
          warnings.warn(
              'Ignoring `unzip` since "{}" does not look like a valid zip file'.format(dest_path))

        os.remove(dest_path)  # delete the zip file.

  @staticmethod
  def _get_confirm_token(response):
    for key, value in response.cookies.items():
      if key.startswith('download_warning'):
        return value
    return None

  @staticmethod
  def _save_response_content(response, destination, showsize, current_size):
    with open(destination, 'wb') as f:
      for chunk in response.iter_content(GoogleDriveDownloader.CHUNK_SIZE):
        if chunk:  # filter out keep-alive new chunks
          f.write(chunk)
          if showsize:
            print(
                '\r' + GoogleDriveDownloader.sizeof_fmt(current_size[0]), end=' ')
            stdout.flush()
            current_size[0] += GoogleDriveDownloader.CHUNK_SIZE

  # From https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
  @staticmethod
  def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
      if abs(num) < 1024.0:
        return '{:.1f} {}{}'.format(num, unit, suffix)
      num /= 1024.0
    return '{:.1f} {}{}'.format(num, 'Yi', suffix)
