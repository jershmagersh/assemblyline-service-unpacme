# UNPACME Service

This Assemblyline service submits PE32 binaries to the [unpac.me](unpac.me) API and provides the results.

**NOTE**: This service **requires** you to have your own API key (Subscription or Community). It is **not** preinstalled during a default installation.

## Execution

This service uploads the provided file to unpac.me using the [unpac.me API](https://api.unpac.me/) and returns the results (if any). Your API key is provided as a parameter which is passed to the service for processing.

Because this service queries an external API, if selected by the user, it will prompt the user and notify them that their file or metadata related to their file will leave our system.

## Testing

In order to run tests for this service, you will first require the AssemblyLine Python packages. These can be installed using the instructions [here](https://cybercentrecanada.github.io/assemblyline4_docs/docs/developer_manual/services/run_your_service.html). Next, your API key must be taken from your [profile](https://www.unpac.me/account#/) and set as the `UPM_API_KEY` environment variable within your terminal. Once done, run the following (in this instance I'm using Python 3.7 which is the official supported version of Python for AssemblyLine): `python3.7 -m unittest test_unpacme_al`. **NOTE**: You must have remaining unpac.me quota in order to run the tests properly.

## Dependencies

The current version of this service makes use of a [third-party library](https://github.com/R3MRUM/unpacme/blob/master/unpacme.py) which is not officially supported by unpac.me. A big shout out to @R3MRUM for writing this library.
