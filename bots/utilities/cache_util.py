import json
import os
import hashlib
from datetime import datetime, timedelta

CACHE_DIR = 'cache'

def get_cache_key(prompt, model):
    """Generate a unique cache key based on the prompt and model."""
    return hashlib.md5(f"{prompt}:{model}".encode()).hexdigest()

def cache_response(prompt, model, response):
    """Cache the API response."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    cache_key = get_cache_key(prompt, model)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    cache_data = {
        'prompt': prompt,
        'model': model,
        'response': response,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f)

def get_cached_response(prompt, model, max_age_hours=24):
    """Retrieve a cached response if available and not expired."""
    cache_key = get_cache_key(prompt, model)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        if datetime.now() - cache_time < timedelta(hours=max_age_hours):
            return cache_data['response']
    
    return None
