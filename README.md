# UNPACME Service

This Assemblyline service submits PE32 binaries to the [unpac.me](unpac.me) API and provides the results.

**NOTE**: This service **requires** you to have your own API key (Subscription or Community). It is **not** preinstalled during a default installation.

## Execution

This service uploads the provided file to unpac.me using the [unpac.me API](https://api.unpac.me/) and returns the results (if any). Simply your API key as a user parameter in order to use the service.

Because this service queries an external API, if selected by the user, it will prompt the user and notify them that their file or metadata related to their file will leave our system.

## Testing

Running tests for this service is very straight forward. First, your API key must be taken from your [profile](https://www.unpac.me/account#/) and set as the `UPM_API_KEY` environment variable within your terminal. Once done, run the following: `python3.7 -m unittest test_unpacme_al`. **NOTE**: You must have remaining quota in order to process the tests properly.

## Dependencies

The current version of this service makes use of a [third-party library](https://github.com/R3MRUM/unpacme/blob/master/unpacme.py) which is not officially supported by unpac.me. This will likely change in the future when the service provides full support for all unpac.me feature sets.
