
import json
import urllib.parse
import boto3
import os
import email


print('Loading function')

s3 = boto3.client('s3')


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    os.chdir("/tmp")

    s3.download_file(bucket, key, "workmail_with_attachment")
    with open("workmail_with_attachment") as f:
        data = f.read()

    message = email.message_from_string(data)

    email_sender = re.sub(r"[^\w]",  '-', message.get("from"))

    if type(message.get_payload()) == list and len(message.get_payload()) == 2:
        attachment = message.get_payload()[1]

        if attachment.get_filename():
            attachment_filename = attachment.get_filename()
