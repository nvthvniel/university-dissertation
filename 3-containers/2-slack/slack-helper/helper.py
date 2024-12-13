import requests, urllib

class helper:

    def api_call(method, payload):
        url = f"https://slack.com/api/{method}"
            
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Slack-No-Retry": "1"}
        payload = urllib.parse.urlencode(payload)

        response = requests.post(url, headers=headers, data=payload)
        response = response.text

        return response