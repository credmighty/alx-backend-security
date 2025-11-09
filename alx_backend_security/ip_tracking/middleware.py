from django.http import HttpResponseForbidden
from .models import RequestLog, BlockedIP
from datetime import datetime
# from ip_geolocation.ip import IPGeolocationAPI
from django.core.cache import cache
from django.contrib.gis.geoip2 import GeoIP2 # used in replacement of ip_geolocation.ip

class IPTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.geo = GeoIP2() # Initialize the geolocation API

    def __call__(self, request):
        #Get IP address
        ip_address = self.get_client_ip(request)
        path = request.path

        # check if IP is blocked
        if BlockedIP.objects.filter(ip_address=ip_address).exists():
            return HttpResponseForbidden('Access Denied: Your IP has been blocked.')
        

        # Get geolocation (cached for 24hrs)
        location_data = cache.get(ip_address)
        if not location_data:
            """data = self.geo.get_geolocation(ip_address)
            country = data.get('country_name', 'Unknown')
            city = data.get('city', 'Unknown')
            location_data = {'country': country, 'city': city}"""
            location_data = self.get_geolocation(ip_address)
            cache.set(ip_address, location_data, timeout=60 * 60 * 24) #24hrs in seconds


        #save request info to database
        RequestLog.objects.create(
            ip_address=ip_address,
            path=path,
            """country=location_data["country"],
            city=location_data["city"],"""
            country=location_data.get("country", "Unknown"),
            city=location_data.get("city", "Unknown"),
        )

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """Get the user's real IP even if behind a proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


    def get_geolocation(self, ip_address):
        try:
            data = self.geo.city(ip_address)
            return {
                "country": data.get("country_name", "Unknown"),
                "city": data.get("city", "Unknown"),
            }
        except Exception:
            return {"country": "Unknown", "city": "Unknown"}