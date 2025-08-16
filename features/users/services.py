import requests

import logging

logger = logging.getLogger(__name__)


# Get the athlete_id from strava_profile_link
def get_strava_athlete_id(strava_profile_link: str) -> str:
    try:
        # Make a GET request but tell it NOT to follow the redirect automatically
        response = requests.head(strava_profile_link)
        logger.info(response.headers)

        # A successful redirect will have a status code in the 3xx range
        # and a 'Location' header with the final URL.
        if response.is_redirect:
            full_url = response.headers.get('Location')
            logger.info(full_url)
            if full_url and 'strava.com/athletes/' in full_url:
                athlete_id = full_url.strip('/').split('?')[0].split('/')[-1]
                logger.debug(f"Resolved URL: {full_url}")
                logger.debug(f"Extracted Athlete ID: {athlete_id}")
                return athlete_id
            else:
                logger.debug("Could not resolve the URL or it was not a valid athlete profile link.")
                return None
        else:
            # This might happen if the link is invalid or doesn't redirect
            logger.debug(f"URL did not redirect. Status: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        # Handle network errors, invalid URLs, etc.
        logger.error(f"An error occurred while trying to resolve the URL: {e}")
        return None