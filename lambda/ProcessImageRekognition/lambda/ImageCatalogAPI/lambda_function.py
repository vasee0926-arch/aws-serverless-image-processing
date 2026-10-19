
import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'ImageLabelsCatalog'


def decimal_to_number(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON serializable"
    )


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body, default=decimal_to_number)
    }


def lambda_handler(event, context):
    try:
        table = dynamodb.Table(TABLE_NAME)

        # HTTP API sends the route and path parameters in these fields.
        method = event.get('requestContext', {}).get(
            'http', {}
        ).get('method', 'GET')

        if method == 'OPTIONS':
            return response(200, {'message': 'OK'})

        path_parameters = event.get('pathParameters') or {}
        image_id = path_parameters.get('image_id')

        if image_id:
            result = table.get_item(
                Key={'image_id': image_id}
            )
            item = result.get('Item')

            if not item:
                return response(404, {
                    'message': 'Image not found',
                    'image_id': image_id
                })

            return response(200, item)

        result = table.scan()
        items = result.get('Items', [])

        # Continue scanning if DynamoDB returns a paginated result.
        while 'LastEvaluatedKey' in result:
            result = table.scan(
                ExclusiveStartKey=result['LastEvaluatedKey']
            )
            items.extend(result.get('Items', []))

        return response(200, {
            'count': len(items),
            'images': items
        })

    except Exception as e:
        print(f"ImageCatalogAPI error: {str(e)}")
        return response(500, {
            'message': 'Internal server error'
        })
