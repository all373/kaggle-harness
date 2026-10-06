"""Read GPU quota; invoke through kaggle_cli.py gpu quota for authentication."""
import json
from datetime import timezone
from zoneinfo import ZoneInfo


def hours(duration):
    return None if duration is None else duration.total_seconds() / 3600


def summarize(response):
    quota = response.gpu_quota
    if quota is None:
        return {'gpu_quota': None}
    used, reserved, allowed = map(hours, (quota.time_used, quota.time_reserved, quota.total_time_allowed))
    refresh = response.quota_refresh_time
    if refresh is not None:
        if refresh.tzinfo is None:
            refresh = refresh.replace(tzinfo=timezone.utc)
        refresh = refresh.astimezone(ZoneInfo('Asia/Tokyo')).isoformat()
    return {'used_hours': used, 'reserved_hours': reserved, 'allowed_hours': allowed,
            'remaining_unreserved_hours': max(0., allowed - used - reserved)
            if None not in (used, reserved, allowed) else None,
            'pay_to_scale_enabled': quota.is_pay_to_scale_enabled, 'refresh_at_jst': refresh}


def main():
    from kaggle.api.kaggle_api_extended import KaggleApi
    from kagglesdk.kernels.types.kernels_api_service import ApiGetAcceleratorQuotaStatisticsRequest
    api = KaggleApi()
    api.authenticate()
    with api.build_kaggle_client() as client:
        response = client.kernels.kernels_api_client.get_accelerator_quota_statistics(
            ApiGetAcceleratorQuotaStatisticsRequest())
    print(json.dumps(summarize(response), indent=2))


if __name__ == '__main__':
    main()
