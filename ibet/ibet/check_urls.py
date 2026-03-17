import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.urls import get_resolver

# Get all URL patterns
resolver = get_resolver()

def get_urls(urlpatterns, prefix=''):
    urls = []
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # This is an included URL module
            urls.extend(get_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
        else:
            urls.append(prefix + str(pattern.pattern))
    return urls

all_urls = get_urls(resolver.url_patterns)
for url in sorted(all_urls):
    print(url)
