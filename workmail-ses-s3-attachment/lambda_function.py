import threading
import json
import urllib.parse
import boto3
from boto3.s3.transfer import S3Transfer, TransferConfig
import os
import email
import re
import sys
import datetime
import requests

print('Loading function')

s3 = boto3.client('s3')
s3_wormhole = S3Transfer(s3,  config=TransferConfig(
    multipart_threshold=8 * 1024 * 1024,
    max_concurrency=10,
    num_download_attempts=10,
))

dest_bucket = "datascience-email-attachment"


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    try:
        # Get the object from the event and show its content type
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(
            event['Records'][0]['s3']['object']['key'], encoding='utf-8')

        os.chdir("/tmp")

        get(bucket, key, "workmail_with_attachment")
        with open("workmail_with_attachment") as f:
            data = f.read()

        message = email.message_from_string(data)

        email_sender = message.get("from")
        if re.search(r'(.*)<.*>', email_sender) and re.search(r'(.*)<.*>', email_sender).group(1):
            email_sender = re.search(r'(.*)<.*>', email_sender).group(1)
            print(email_sender)

        email_sender = format_string_for_s3_bucket_name(email_sender)

        email_subject = format_string_for_s3_bucket_name(
            message.get('Subject'))

        now = datetime.datetime.now()
        now = f"{str(now.year)}/{str(now.month).zfill(2)}/{str(now.day).zfill(2)}"

        dest_bucket_key = f"{email_sender}/{email_subject}/{now}"

        if type(message.get_payload()) == list and len(message.get_payload()) == 2:
            attachment = message.get_payload()[1]

            if attachment.get_filename():
                attachment_filename = attachment.get_filename()

                with open(attachment_filename, 'wb') as f:
                    f.write(attachment.get_payload(decode=True))

                print(
                    f"Putting file {attachment_filename} to {dest_bucket}/{dest_bucket_key}")
                put(attachment_filename,
                    dest_bucket, f"{dest_bucket_key}/{attachment_filename}")

    except Exception as e:
        print(str(e))
        slack_notification(str(e))


def format_string_for_s3_bucket_name(bucket_name):
    found = re.sub(r"[^\w]",  ' ', bucket_name)
    found = re.sub(r"\s+", ' ', found).strip()
    print(found)
    print(re.sub(r"[^\w]",  '-', found))
    bucket_name = re.sub(r"[^\w]",  '-', found)
    print(bucket_name)
    return bucket_name


def get(bucket, key, local_path):
    """Download s3://bucket/key to local_path'."""
    try:
        s3_wormhole.download_file(
            bucket=bucket, key=key, filename=local_path)
    except Exception as e:
        print(
            "Could not get {} from S3 due to {}".format(key, e))
        return None
    else:
        print("Successfully get {} from S3".format(key))
    return key


def put(local_path, bucket, key):
    """Upload local_path to s3: // bucket/key and print upload progress."""
    try:

        s3_wormhole.upload_file(filename=local_path,
                                bucket=bucket,
                                key=key,
                                callback=ProgressPercentage(local_path))
    except Exception as e:
        print(
            "Could not upload {} to S3 due to {}".format(key, e))
    else:
        print("Successfully uploaded {} to S3".format(key))


def slack_notification(message):
    base_uri = "http://slack.datascience.ec2/postMessage"
    warningTemplateMessage = {
        "text": "<!here> Error: Athena runner email trigger {}  "}

    headers = {'Content-Type': 'application/json'}

    warningMessage = {}
    warningMessage['text'] = warningTemplateMessage['text'].format(
        str(message))

    resp = requests.post(base_uri, headers=headers,
                         data=json.dumps(warningMessage))

    return resp


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (self._filename, self._seen_so_far,
                                             self._size, percentage))
            sys.stdout.flush()
