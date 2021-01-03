# unpacme
Python3 interface for the unpac.me binary unpacking service

https://www.unpac.me/

# Supported functions
* **upload_file** - Upload a single file
* **upload_dir** - Upload all files contained within a specified directory
* **get_analysis_report** - Retrieve analysis results for a given submission
* **download_sample** - Download a sample matching a given sha256 hash
* **get_history** - Retrieves your submission history
* **get_public_feed** - Retrieves the public feed data
* **search_hash** - Retrieves information for a given hash
* **get_remaining_quota** - Retrieves API quota remaining

# Basic file upload implementation example:
```Python
#!/usr/bin/python3

from unpacme import unpacme

unpac = unpacme('YOUR_API_KEY_HERE')
path = '/home/<user>/Desktop/sample.bin'
response = unpac.upload_file(path)
print(response)
```
# Example output:
```bash
$ ./upload_test.py 
{'filename': 'sample.bin', 'filesize': 382464, 'success': True, 'id': '00000000-1111-2222-3333-444444444444'}
```
