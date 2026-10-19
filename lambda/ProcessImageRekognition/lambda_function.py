import json
import boto3
import urllib.parse
import time
from datetime import datetime, timezone
from decimal import Decimal

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = 'ImageLabelsCatalog'
SNS_TOPIC_ARN = (
    'arn:aws:sns:us-east-1:175640206114:ImageProcessedAlerts'
)
PROCESSED_BUCKET = 'rekognition-lab-processed-yourname-2026'


def lambda_handler(event, context):
    print("Received SQS event:")
    print(json.dumps(event))

    table = dynamodb.Table(TABLE_NAME)

    for record in event.get('Records', []):
        start_time = time.time()
        key = None

        try:
            # 1. Read the original S3 event from the SQS message
            s3_event = json.loads(record['body'])
            s3_record = s3_event['Records'][0]

            upload_timestamp = s3_record.get(
                'eventTime',
                datetime.now(timezone.utc).isoformat()
            )

            bucket = s3_record['s3']['bucket']['name']

            key = urllib.parse.unquote_plus(
                s3_record['s3']['object']['key'],
                encoding='utf-8'
            )

            print(f"Processing image: s3://{bucket}/{key}")

            # 2. Mark the image as PROCESSING
            table.update_item(
                Key={'image_id': key},
                UpdateExpression='SET processing_status = :status',
                ExpressionAttributeValues={
                    ':status': 'PROCESSING'
                }
            )

            print(f"Status updated to PROCESSING for {key}")

            # 3. Analyse the image with Rekognition
            rekog_response = rekognition.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                MaxLabels=10,
                MinConfidence=75
            )

            labels = [
                {
                    'name': label['Name'],
                    'confidence': round(label['Confidence'], 2)
                }
                for label in rekog_response['Labels']
            ]

            label_names = [label['name'] for label in labels]
            print(f"Detected labels: {label_names}")

            # 4. Calculate processing duration and timestamp
            processing_duration = round(
                (time.time() - start_time) * 1000,
                2
            )

            timestamp = datetime.now(timezone.utc).isoformat()

            # 5. Create the processed JSON result
            result = {
                'image_id': key,
                'input_bucket': bucket,
                'processed_bucket': PROCESSED_BUCKET,
                'processing_status': 'COMPLETED',
                'detected_labels': labels,
                'label_count': len(labels),
                'processing_duration_ms': processing_duration,
                'processed_timestamp': timestamp
            }

            result_key = (
                'processed/' + key.replace('/', '_') + '.json'
            )

            # 6. Store the result in the processed S3 bucket
            s3.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=result_key,
                Body=json.dumps(result, indent=2),
                ContentType='application/json'
            )

            print(
                f"Processed result stored at "
                f"s3://{PROCESSED_BUCKET}/{result_key}"
            )

            # 7. Store metadata in DynamoDB
            table.put_item(
                Item={
                    'image_id': key,
                    'bucket_name': bucket,
                    'processed_bucket': PROCESSED_BUCKET,
                    'processing_status': 'COMPLETED',
                    'detected_labels': label_names,
                    'label_count': len(label_names),
                    'upload_timestamp': upload_timestamp,
                    'processing_duration_ms': Decimal(
                        str(processing_duration)
                    ),
                    'processing_timestamp': timestamp,
                    'result_location': result_key
                }
            )

            print(f"DynamoDB metadata stored for {key}")

            # 8. Send SNS notification
            sns_response = sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='Image Processing Completed',
                Message=(
                    f"Image: {key}\n"
                    f"Status: COMPLETED\n"
                    f"Labels: {', '.join(label_names)}\n"
                    f"Label Count: {len(label_names)}\n"
                    f"Processing Time: {processing_duration} ms\n"
                    f"Result: s3://{PROCESSED_BUCKET}/{result_key}"
                )
            )

            print(
                f"SNS notification sent successfully. "
                f"MessageId: {sns_response['MessageId']}"
            )
            print(f"Successfully processed: {key}")

        except Exception as e:
            print(f"ERROR processing record for image {key}: {str(e)}")

            # 9. Mark the image as FAILED, if its key was identified
            if key is not None:
                try:
                    table.update_item(
                        Key={'image_id': key},
                        UpdateExpression=(
                            'SET processing_status = :status'
                        ),
                        ExpressionAttributeValues={
                            ':status': 'FAILED'
                        }
                    )
                    print(f"Status updated to FAILED for {key}")

                except Exception as status_error:
                    print(
                        f"Could not update FAILED status for {key}: "
                        f"{str(status_error)}"
                    )

            # Critical: let Lambda/SQS know the message failed.
            # SQS can retry it and eventually move it to the DLQ.
            raise

    return {
        'statusCode': 200,
        'body': json.dumps(
            'Image processing completed successfully'
        )
    }
