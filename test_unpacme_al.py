#!/usr/bin/env python

import unittest
from unpacme_al import UnpacMeAL
from unpacme import unpacme
import os
from assemblyline_v4_service.common.result import Result
from assemblyline_v4_service.common.request import ServiceRequest
from assemblyline.odm.messages.task import Task as ServiceTask
from assemblyline_v4_service.common.task import Task
import cart

API_KEY = os.environ.get('UPM_API_KEY', "InvalidKey!")
TEST_BINARY_PATH = 'examples/11b2e4900959874f4a335514c58c2ded88a3268b099984745e4c36d5ae434ea3.cart'

# Stolen from
# https://github.com/CybercentreCanada/assemblyline-service-characterize/
# blob/c5295ca900ff319c5e80b10382cdd7652c61eb2b/test/test_service.py#L16
sample1 = dict(
    sid=1,
    metadata={},
    service_name='characterize',
    service_config={},
    fileinfo=dict(
        magic='ASCII text, with no line terminators',
        md5='1f09ecbd362fa0dfff88d4788e6f5df0',
        mime='text/plain',
        sha1='a649bf201cde05724e48f2d397a615b201be34fb',
        sha256='dadc624d4454e10293dbd1b701b9ee9f99ef83b4cd07b695111d37eb95abcff8',
        size=19,
        type='unknown',
    ),
    filename='dadc624d4454e10293dbd1b701b9ee9f99ef83b4cd07b695111d37eb95abcff8',
    min_classification='TLP:WHITE',
    max_files=501,  # TODO: get the actual value
    ttl=3600,
)


class TestResults(unittest.TestCase):
    presults = None
    upm = unpacme.UnpacMe(API_KEY)
    upmal = UnpacMeAL()

    def test_upload_proc_results(self):
        upm = unpacme.UnpacMe(API_KEY)

        # We need to decrypt the cart format to process the sample.
        cart.unpack_file(TEST_BINARY_PATH, "{}_dec".format(TEST_BINARY_PATH))
        record = upm.upload_file("{}_dec".format(TEST_BINARY_PATH))
        if record['success']:
            os.remove("{}_dec".format(TEST_BINARY_PATH))
            api_response = self.upmal.wait_for_completion(upm, record)
            self.proc_results(api_response)
            self.gen_results(api_response)

    def proc_results(self, api_response):
        # Make sure general processing is working.
        procr = self.upmal.process_results(api_response, self.upm)
        self.assertTrue(procr['unpacked'])

        # Make sure resulting samples downloaded properly.
        for sample in procr['unpacked_samples']:
            self.assertTrue(os.path.exists(sample['data_path']))

    def gen_results(self, api_response):
        procr = self.upmal.process_results(api_response, self.upm)
        result = Result()
        service_task = ServiceTask(sample1)
        task = Task(service_task)
        request = ServiceRequest(task)
        self.upmal.generate_results(procr, result, api_response, request)
