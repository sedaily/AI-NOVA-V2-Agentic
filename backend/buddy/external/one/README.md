# buddy Service - external - one Card(s)

## Purpose
This service provides buddy functionality for external users with one card configuration.

## Card Configuration
- **Number of cards**: one
- **Target audience**: external
- **Service type**: buddy

## API Endpoint
`POST /buddy/external/one`

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
  "service": "buddy",
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
