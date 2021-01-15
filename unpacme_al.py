import json
from unpacme import unpacme
import time

from assemblyline_v4_service.common.base import ServiceBase
from assemblyline_v4_service.common.result import Result, ResultSection, BODY_FORMAT, Heuristic

MAX_TIMEOUT = 300
TIMEOUT_INCREMENT = 15

class UnpacMeAL(ServiceBase):
    environments = {}
    compiled_rules = None

    def __init__(self, config=None):
        super(UnpacMeAL, self).__init__(config)

    def start(self):
        self.log.info(f"start() from {self.service_attributes.name} service called")

    def filetype_check(self, request):
        valid_filetype = False

        if request.file_type == 'executable/windows/pe32':
            valid_filetype = True

        return valid_filetype

    def prechecks(self, request, api_key):
        passed_prechecks = True

        if not self.filetype_check(request):
            self.log.error(f"UNPACME currently only supports 32-bit Portable Executables.")
            passed_prechecks = False
        # Accessing the service request object results in an exception
        # regardless of this not existing.
        if not api_key or api_key == '':
            self.log.error(f"An API key is required to make API calls to UNPACME.")
            passed_prechecks = False

        return passed_prechecks

    def check_status(self, upm, rid):
        status = upm.get_analysis_report(rid)
        rstatus = None
        if status == 'validating' or status == 'unpacking':
            rstatus = None
        # Results from the UNPACME library will be stored in a dictionary
        # once the run is complete.
        elif type(status) is dict:
            rstatus = status

        return rstatus

    def wait_for_completion(self, upm, record):
        total = 0
        status = None
        while(not status):
            status = self.check_status(upm, record['id'])
            if status:
                break
            time.sleep(TIMEOUT_INCREMENT)
            total += TIMEOUT_INCREMENT
            if total > MAX_TIMEOUT:
                self.log.error(f"Maximum timeout reached for processing of sample.")
                break
        return status

    def process_results(self, analysis_results, upm):
        results = {
            'unpacked': False,
            'unpacked_samples': []
        }

        if len(analysis_results['results']) > 1:
            results['unpacked'] = True

        for ar in analysis_results['results']:
            downloaded = upm.download_sample(ar['hashes']['sha256'], self.working_directory)
            dl_path = None
            if downloaded:
                dl_path = "{}/{}.bin".format(self.working_directory, ar['hashes']['sha256'])

            results['unpacked_samples'].append({
                'sha256': ar['hashes']['sha256'],
                'malware_id': ar['malware_id'],
                'data_path': dl_path
            })

        return results

    def generate_results(self, presults, result, analysis_results, request):
        if presults['unpacked']:
            result.add_section(ResultSection("Successully unpacked binary.", heuristic=Heuristic(1)))

        for r in presults['unpacked_samples']:
            if len(r['malware_id']) > 0:
                for rm in r['malware_id']:
                    section = ResultSection("{} - {}".format(r['sha256'], rm['name']), heuristic=Heuristic(2))
                    section.add_line("Details: {}".format(rm['reference']))
                    result.add_section(section)
            request.add_extracted(r['data_path'], r['sha256'], f'Unpacked from {request.sha256}')

        result.add_section(ResultSection(f"UNPACME Detailed Results", body_format=BODY_FORMAT.JSON,
                                                body=json.dumps(analysis_results['results'])))

        return result, request
                
    def execute(self, request):
        # Result Object
        result = Result()
        api_key = request.get_param("api_key")

        presults = None
        if self.prechecks(request, api_key):
            upm = unpacme.unpacme(api_key)
            record = upm.upload_file(request.file_path)
            if record['success']:
                analysis_results = self.wait_for_completion(upm, record)
                if analysis_results:
                    presults = self.process_results(analysis_results, upm)
                    result, request = self.generate_results(presults, result, analysis_results, request)
            else:
                self.log.error(f"An exception occurred while uploading the sample to UNPACME: %s" % record['msg'])

        request.result = result
