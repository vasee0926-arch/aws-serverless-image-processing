# Testing

## Successful Processing

1. Upload an image to the S3 input bucket.
2. S3 sends an event to Amazon SQS.
3. SQS invokes the processing Lambda.
4. Amazon Rekognition detects labels.
5. Processing results are stored in the processed S3 bucket.
6. Metadata is stored in DynamoDB.
7. SNS sends an email notification.

## Failure Handling

Failed SQS messages are retried and can be routed to the configured Dead Letter Queue (DLQ).

## API Testing

The API was tested using GET requests through API Gateway.

The `/images` endpoint successfully returns image catalog information from DynamoDB.
