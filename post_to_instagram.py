"""
Lafz o Khayal — Instagram publisher.
Publishes an already-hosted image (public URL) to Instagram via the Graph API.

Required environment variables:
  IG_USER_ID       - your Instagram Business Account ID (the long number)
  IG_ACCESS_TOKEN  - your long-lived access token
  IMAGE_URL        - public URL of the image to post
  CAPTION_FILE     - path to a text file containing the caption
"""
import os
import sys
import time
import json
import urllib.request
import urllib.parse

API = "https://graph.facebook.com/v21.0"


def api_post(path, params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{API}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def api_get(path, params):
    qs = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{API}/{path}?{qs}") as r:
        return json.loads(r.read())


def main():
    ig_user = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    image_url = os.environ["IMAGE_URL"]
    caption = open(os.environ["CAPTION_FILE"], encoding="utf-8").read()

    # Step 1: create a media container
    print("Creating media container...")
    container = api_post(f"{ig_user}/media", {
        "image_url": image_url,
        "caption": caption,
        "access_token": token,
    })
    container_id = container["id"]
    print(f"Container: {container_id}")

    # Step 2: wait until the container is ready
    for _ in range(20):
        status = api_get(container_id, {
            "fields": "status_code", "access_token": token})
        code = status.get("status_code")
        print(f"Status: {code}")
        if code == "FINISHED":
            break
        if code == "ERROR":
            print("Container processing failed.", file=sys.stderr)
            sys.exit(1)
        time.sleep(5)

    # Step 3: publish
    print("Publishing...")
    result = api_post(f"{ig_user}/media_publish", {
        "creation_id": container_id,
        "access_token": token,
    })
    print(f"Published! Media ID: {result['id']}")


if __name__ == "__main__":
    main()
