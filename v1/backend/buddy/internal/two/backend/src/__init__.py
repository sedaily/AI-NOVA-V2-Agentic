"""
Nexus Backend Package
3-Tier Architecture Implementation
"""

# Version
__version__ = '1.0.0'

# Package imports
from .models import *
from .repositories import *
from .services import *
from .config import *

__all__ = [
    '__version__',
    # Models
    'Conversation',
    'Message',
    'Prompt',
    'PromptConfig',
    'PromptFile',
    'Usage',
    'UsageSummary',
    # Repositories
    'ConversationRepository',
    'PromptRepository',
    'UsageRepository',
    # Services
    'ConversationService',
    'PromptService',
    'UsageService',
    # Config
    'TABLES',
    'AWS_REGION',
    'DYNAMODB_CONFIG',
    'BEDROCK_CONFIG',
    'API_GATEWAY_CONFIG',
    'LAMBDA_CONFIG'
]