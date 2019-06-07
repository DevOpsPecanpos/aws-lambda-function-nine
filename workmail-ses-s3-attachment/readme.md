# Athena s3 email 

This lambda function is to extract AWS Workmail email attachment to a separated s3 bucket by setting up AWS SES receving rule set. The workflow is: emails will be sent to AWS Workmail email address. AWS SES email receiving rule set can place all those emails to a linked s3 bucket. Once we receive the workmail in the linked S3 bucket, that bucket with this lambda function will be triggered to extract the attachment from the email and place it to another separated s3 bucket according to the sender-name/email-subject/year/month/day as s3 folder structure. . Then a file-transfer will be needed be set up to transfer the files to athena folder.

<br/>
 
Run below code to get all the dependencies for the code : 
```
pip install -r requirements.txt -t ./
chmod 777 lambda_function.py
zip -r9 ../lambda_function.zip .
```

<br/>

Then upload the lambda_function.zip