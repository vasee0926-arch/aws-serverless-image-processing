# System Architecture

The platform follows a serverless event-driven architecture.

## Processing Pipeline

Amazon S3 → Amazon SQS → AWS Lambda → Amazon Rekognition

The Lambda function stores processing results in Amazon S3 and DynamoDB and sends notifications through Amazon SNS.

## API Layer

API Gateway → ImageCatalogAPI Lambda → DynamoDB

The API provides access to the processed image catalog without directly exposing the DynamoDB table.
