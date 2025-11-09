from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from ip_tracking.models import RequestLog, SuspiciousIP

@shared_task
def detect_suspicious_ips():
    """
    Detect and flag suspicious IPs every hour:
    - >100 requests in the past hour
    - Accessing sensitive paths (/admin, /login)
    """
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)

    # 1️⃣ Check for high-traffic IPs
    high_traffic = (
        RequestLog.objects
        .filter(timestamp__gte=one_hour_ago)
        .values('ip_address')
        .annotate(count=models.Count('ip_address'))
        .filter(count__gt=100)
    )

    for entry in high_traffic:
        ip = entry['ip_address']
        reason = f"Exceeded 100 requests in the past hour ({entry['count']})"
        SuspiciousIP.objects.get_or_create(ip_address=ip, defaults={'reason': reason})

    # 2️⃣ Check for sensitive path access
    sensitive_paths = ['/admin', '/login']
    suspicious_access = (
        RequestLog.objects
        .filter(path__in=sensitive_paths, timestamp__gte=one_hour_ago)
        .values_list('ip_address', flat=True)
        .distinct()
    )

    for ip in suspicious_access:
        reason = "Accessed sensitive path (/admin or /login)"
        SuspiciousIP.objects.get_or_create(ip_address=ip, defaults={'reason': reason})
