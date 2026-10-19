# AWS Serverless Image Processing Platform

A serverless, event-driven image processing platform built using AWS managed services. The system automatically processes uploaded images, detects objects and scenes using Amazon Rekognition, stores processing results, maintains an image catalog in DynamoDB, and sends email notifications through Amazon SNS.

## Architecture

```text
User
 │
 ▼
Amazon S3
Input Bucket
 │
 ▼
Amazon SQS
ImageProcessingQueue
 │
 ▼
AWS Lambda
ProcessImageRekognition
 │
 ├──────────────► Amazon Rekognition
 │                    │
 │                    ▼
 │              Detected Labels
 │
 ├──────────────► S3 Processed Bucket
 │
 ├──────────────► DynamoDB
 │                ImageLabelsCatalog
 │
 └──────────────► Amazon SNS
                       │
                       ▼
                  Email Alert


API Client
 │
 ▼
Amazon API Gateway
 │
 ▼
ImageCatalogAPI Lambda
 │
 ▼
Amazon DynamoDB
