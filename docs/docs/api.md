# API Documentation

## GET /images

Returns the processed image catalog.

### Response

The API returns:

- image_id
- detected_labels
- label_count
- processing_status
- processing_duration_ms
- bucket_name
- processed_bucket
- upload_timestamp
- processing_timestamp
- result_location

## GET /images/{image_id}

Returns information about a specific processed image.

### Data Source

Amazon DynamoDB (`ImageLabelsCatalog`)
