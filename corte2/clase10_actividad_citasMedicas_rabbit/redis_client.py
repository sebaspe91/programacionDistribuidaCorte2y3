import redis

# Conexión a Redis (coordinador de locks)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

