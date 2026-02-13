# foreign Service - external - one Card(s)

## Purpose
This service provides foreign functionality for external users with one card configuration.

## Card Configuration
- **Number of cards**: one
- **Target audience**: external
- **Service type**: foreign

## API Endpoint
`POST /foreign/external/one`

## Request Format
```json
{
  "text": "Input text for processing",
  "options": {}
}
```

## Response Format
```json
{
  "service": "foreign",
  "audience": "external", 
  "cards": "one",
  "result": "Processed result"
}
```

## Development
```bash
# Install dependencies
npm install

# Deploy to dev
serverless deploy --stage dev

# Deploy to production
serverless deploy --stage prod
```

## Prompts
- `prompts/system.txt`: System prompt for AI model
- `prompts/user.txt`: User prompt template
