import json
import base64
import boto3
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
polly_client = boto3.client('polly')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    AWS Lambda function to convert text to speech using Amazon Polly
    """
    
    # Set CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle OPTIONS request for CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS preflight'})
        }
    
    try:
        # Parse request body
        if event.get('body'):
            if event.get('isBase64Encoded'):
                body = base64.b64decode(event['body']).decode('utf-8')
            else:
                body = event['body']
            
            request_data = json.loads(body)
        else:
            request_data = event
        
        # Extract text and voice parameters
        text = request_data.get('text', '').strip()
        voice = request_data.get('voice', 'Joanna')
        
        # Validate input
        if not text:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'No text provided'
                })
            }
        
        if len(text) > 3000:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Text exceeds 3000 character limit'
                })
            }
        
        # Valid voices list
        valid_voices = [
            'Joanna', 'Matthew', 'Amy', 'Brian', 'Mia', 
            'Ricardo', 'Lucia', 'Lea', 'Kimberly', 'Justin',
            'Ivy', 'Joey', 'Salli', 'Kendra', 'Nicole'
        ]
        
        if voice not in valid_voices:
            voice = 'Joanna'  # Default voice
        
        logger.info(f"Generating speech for text length: {len(text)}, voice: {voice}")
        
        # Generate speech using Polly
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice,
            Engine='standard'  # Use neural engine for better quality
        )
        
        # Read audio stream
        audio_stream = response['AudioStream'].read()
        
        # Convert to base64 for easy transmission
        audio_base64 = base64.b64encode(audio_stream).decode('utf-8')
        
        logger.info("Speech synthesis completed successfully")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'audioData': audio_base64,
                'voiceUsed': voice,
                'textLength': len(text),
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Audio generated successfully'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in Lambda function: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        }