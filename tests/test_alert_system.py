"""Tests for alert system"""

import pytest
from src.alerts.alert_system import AlertSystem


@pytest.mark.asyncio
async def test_price_change_alert():
    """Test price change detection"""
    alert_system = AlertSystem()
    alert_system.price_change_threshold = 5.0  # 5% threshold

    # First update - no alert
    alert1 = await alert_system.check_price_change('market-1', 'Test Market', 50.0)
    assert alert1 is None

    # Small change - no alert
    alert2 = await alert_system.check_price_change('market-1', 'Test Market', 52.0)
    assert alert2 is None

    # Large change - should alert
    alert3 = await alert_system.check_price_change('market-1', 'Test Market', 60.0)
    assert alert3 is not None
    assert alert3.alert_type == 'price_change'
    assert 'increased' in alert3.message.lower()


@pytest.mark.asyncio
async def test_volume_spike_alert():
    """Test volume spike detection"""
    alert_system = AlertSystem()
    alert_system.volume_spike_threshold = 10000.0  # $10k threshold

    # First update - no alert
    alert1 = await alert_system.check_volume_spike('market-1', 'Test Market', 5000.0)
    assert alert1 is None

    # Small increase - no alert
    alert2 = await alert_system.check_volume_spike('market-1', 'Test Market', 8000.0)
    assert alert2 is None

    # Large spike - should alert
    alert3 = await alert_system.check_volume_spike('market-1', 'Test Market', 20000.0)
    assert alert3 is not None
    assert alert3.alert_type == 'volume_spike'


def test_get_recent_alerts():
    """Test getting recent alerts"""
    alert_system = AlertSystem()

    # Add some mock alerts
    for i in range(20):
        from src.alerts.alert_system import Alert
        from datetime import datetime

        alert = Alert(
            timestamp=datetime.now(),
            alert_type='test',
            market_id=f'market-{i}',
            market_question='Test',
            message=f'Alert {i}',
            severity='info',
            data={}
        )
        alert_system.alert_history.append(alert)

    recent = alert_system.get_recent_alerts(limit=5)
    assert len(recent) == 5
    assert recent[-1].message == 'Alert 19'
