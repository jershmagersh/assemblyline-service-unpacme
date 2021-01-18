#!/usr/bin/python3

import requests
from os import listdir
from os.path import isdir, isfile, join, basename
import logging
from time import sleep
import sys


class UnpacMe(object):

    def __init__(self, api_key=None):

        self.API_KEY = api_key
        self.__API_TARGET = 'https://api.unpac.me/api/v1'
        self.RATE_LIMIT = 5

    def upload_file(self, path):

        if self.API_KEY is None:
            logging.error('In order to upload files to unpac.me, you must have a valid API key configured.')
            return None

        if isdir(path):
            logging.error('The path specified appears to be a directory and not a file.')
            return None
        elif not isfile(path):
            logging.error('The file specified for upload does not exist.')
            return None

        logging.debug(f'Reading {basename(path)} into memory.')
        with open(path, "rb") as f:
            file_data = f.read()

        file_size = len(file_data)

        record = {'filename': basename(path), 'filesize': file_size}

        auth_header = {'Authorization': f'Key {self.API_KEY}'}
        files = {'file': (basename(path), file_data)}

        logging.info('Uploading %s (%s bytes) to unpac.me' % (path, file_size))

        try:
            response = requests.post(f'{self.__API_TARGET}/private/upload', files=files, headers=auth_header)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(f'File upload failed with the following error: {err}.')
            record['success'] = False
            record['msg'] = err
            return record
        except requests.exceptions.Timeout:
            logging.error('File upload timed out.')
            record['success'] = False
            record['msg'] = 'timed out'
            return record
        except requests.exceptions.RequestException as err:
            logging.error(f'File upload failed with the following error: {err}.')
            record['success'] = False
            record['msg'] = err
            return record

        if 'id' not in response.json():
            logging.error('The upload appears to have failed as an ID value was not returned from the server.')
            record['success'] = False
            record['msg'] = 'no id'
        else:
            submission_id = response.json()['id']
            logging.debug(f'Upload succeeded. The submission ID is {submission_id}.')
            record['success'] = True
            record['id'] = submission_id

        return record

    def upload_dir(self, path):

        if self.API_KEY is None:
            logging.error('In order to upload files to unpac.me, you must have a valid API key configured.')
            return None

        if isfile(path):
            logging.error('The path specified appears to be a file and not a directory.')
            return None
        elif not isdir(path):
            logging.error('The directory specified does not exist.')
            return None

        files = [f for f in listdir(path) if isfile(join(path, f))]
        remaining_quota = self.get_remaining_quota()

        if len(files) > remaining_quota:
            logging.error(f'Insufficient quota: You are attempting to upload {len(files)} '
                          f'files but you only have {remaining_quota} private API requests remaining. '
                          f'Please remove {len(files) - remaining_quota} files from the directory '
                          f'before trying again.')
            return None

        results = list()

        for file in files:
            full_path_and_filename = join(path, file)

            with open(full_path_and_filename, "rb") as f:
                file_data = f.read()

            file_size = len(file_data)

            record = {'filename': file, 'filesize': file_size}

            auth_header = {'Authorization': f'Key {self.API_KEY}'}
            files = {'file': (basename(path), file_data)}

            response = None
            logging.info('Uploading %s' % path)

            try:
                response = requests.post(f'{self.__API_TARGET}/private/upload', files=files, headers=auth_header)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                logging.error(f'File upload failed with the following error: {err}.')
                record['success'] = False
                record['msg'] = err
            except requests.exceptions.Timeout:
                logging.error('File upload timed out.')
                record['success'] = False
                record['msg'] = 'timed out'
            except requests.exceptions.RequestException as err:
                logging.error(f'File upload failed with the following error: {err}.')
                record['success'] = False
                record['msg'] = err

            if 'id' not in response.json():
                logging.error('The upload appears to have failed as an ID value was not returned from the server.')
                record['success'] = False
                record['msg'] = 'no id'
            else:
                submission_id = response.json()['id']
                logging.debug(f'Upload succeeded. The submission ID is {submission_id}.')
                record['success'] = True
                record['id'] = submission_id

            results.append(record)

            if len(results) < len(files):
                sleep(self.RATE_LIMIT)

        return results

    def __get_analysis_status(self, analysis_id):

        try:
            response = requests.get(f'{self.__API_TARGET}/public/status/{analysis_id}')
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(f'Status check for {analysis_id} failed: {err}.')
            return False
        except requests.exceptions.Timeout:
            logging.error(f'Status check for {analysis_id} timed out.')
            return False
        except requests.exceptions.RequestException as err:
            logging.error(f'Status check for {analysis_id} failed: {err}.')
            return False

        return response.json().get('status', False)

    def get_analysis_report(self, analysis_id):

        logging.info(f'Retrieving analysis status for {analysis_id}.')
        status = self.__get_analysis_status(analysis_id)

        if status == 'fail':
            logging.info(f'Analysis for {analysis_id} has failed.')
            return status

        if status != 'complete':
            logging.info(f'Analysis for {analysis_id} has not yet completed. Current status: {status}.')
            return status

        logging.info(f'Analysis for {analysis_id} has completed. Retrieving report.')

        try:
            response = requests.get(f'{self.__API_TARGET}/public/results/{analysis_id}')
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(f'Report retrieval for {analysis_id} failed: {err}.')
            return False
        except requests.exceptions.Timeout:
            logging.error(f'Report retrieval for {analysis_id} timed out.')
            return False
        except requests.exceptions.RequestException as err:
            logging.error(f'Report retrieval for {analysis_id} failed: {err}.')
            return False

        return response.json()

    def download_sample(self, sample_sha256, dest_path):

        if self.API_KEY is None:
            logging.error('In order to download files from unpac.me, you must have a valid API key configured.')
            return False

        if isfile(dest_path):
            logging.error('The path specified appears to be a file and not a directory.')
            return False
        elif not isdir(dest_path):
            logging.error('The directory specified does not exist.')
            return False

        auth_header = {'Authorization': f'Key {self.API_KEY}'}
        logging.info(f'Downloading {sample_sha256}.')

        try:
            response = requests.get(f'{self.__API_TARGET}/private/download/{sample_sha256}', headers=auth_header)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(f'File download failed with the following {err}.')
            return False
        except requests.exceptions.Timeout:
            logging.error('File download timed out.')
            return False
        except requests.exceptions.RequestException as err:
            logging.error(f'File download failed with the following {err}.')
            return False

        sample_data = response.content
        data_len = len(sample_data)

        if data_len > 0:
            full_path_and_filename = join(dest_path,  f'{sample_sha256}.bin')
            logging.info(f'Writing {data_len} bytes to {full_path_and_filename}')

            with open(full_path_and_filename, "wb") as f:
                f.write(sample_data)
            logging.info(f'{sample_sha256}.bin successfully written to {dest_path}.')
            return True
        else:
            logging.error('File download failed. 0 bytes returned from the server.')
            return False

    def get_history(self, cursor=None, limit=None):

        if self.API_KEY is None:
            logging.error('In order to download files to unpac.me, you must have a valid API key configured.')
            return False

        auth_header = {'Authorization': f'Key {self.API_KEY}'}
        query = ''

        if limit and cursor:
            query = f'?limit={limit}&cursor={cursor}'
        elif limit and not cursor:
            query = f'?limit={limit}'
        elif cursor and not limit:
            query = f'?cursor={cursor}'

        logging.info('Retrieving submission history')
        try:
            response = requests.get(f'{self.__API_TARGET}/private/history{query}', headers=auth_header)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(f'History retrieval failed with the following error: {err}.')
            return False
        except requests.exceptions.Timeout:
            logging.error('History retrieval timed out')
            return False
        except requests.exceptions.RequestException as err:
            logging.error(f'History retrieval failed with the following error: {err}.')
            return False

        return response.json()

    def get_public_feed(self):

        logging.info('Retrieving public feed')

        try:
            response = requests.get(f'{self.__API_TARGET}/public/feed')
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(f'Public feed retrieval failed with the following error: {err}.')
            return False
        except requests.exceptions.Timeout:
            logging.error('Public feed retrieval timed out.')
            return False
        except requests.exceptions.RequestException as err:
            logging.error(f'Public feed retrieval failed with the following error: {err}.')
            return False

        return response.json()

    def search_hash(self, sample_sha256):
        if self.API_KEY is None:
            logging.error('In order to search for hashes, you must have a valid API key configured.')
            return False

        auth_header = {'Authorization': f'Key {self.API_KEY}'}

        logging.info(f'Searching for the hash: {sample_sha256}.')

        try:
            response = requests.get(f'{self.__API_TARGET}/private/search/hash/{sample_sha256}', headers=auth_header)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(f'Sample hash search failed with the following error: {err}.')
            return False
        except requests.exceptions.Timeout:
            logging.error('Sample hash search timed out.')
            return False
        except requests.exceptions.RequestException as err:
            logging.error(f'Sample hash search failed with the following error: {err}.')
            return False

        return response.json().get('results', False)

    def __get_stats(self):

        if self.API_KEY is None:
            logging.error('In order to check account stats, you must have a valid API key configured.')
            return None

        auth_header = {'Authorization': f'Key {self.API_KEY}'}
        logging.info('Retrieving account stats.')

        try:
            response = requests.get(f'{self.__API_TARGET}/private/user/access', headers=auth_header)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(f'Account stats retrieval failed with the following error: {err}.')
            return None
        except requests.exceptions.Timeout:
            logging.error('Account stats retrieval timed out.')
            return None
        except requests.exceptions.RequestException as err:
            logging.error(f'Account stats retrieval failed with the following error: {err}.')
            return None

        return response.json()

    def get_remaining_quota(self):
        stats = self.__get_stats()

        if 'month_limit' in stats and 'month_submissions' in stats:
            return stats['month_limit'] - stats['month_submissions']
        else:
            logging.error('Monthly limit and submission data not present in response returned from the server.')
            return None
