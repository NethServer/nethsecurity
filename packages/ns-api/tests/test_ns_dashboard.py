import importlib.util
import sys
import types
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / 'files' / 'ns.dashboard'


def load_module():
    fake_euci = types.ModuleType('euci')

    class DummyEUci:
        def get(self, *args, **kwargs):
            return ''

        def get_all(self, *args, **kwargs):
            return {}

    fake_euci.EUci = DummyEUci

    fake_utils = types.SimpleNamespace(
        get_all_wan_devices=lambda *args, **kwargs: [],
        get_interface_from_device=lambda *args, **kwargs: '',
        get_all_by_type=lambda *args, **kwargs: {},
    )
    fake_ovpn = types.SimpleNamespace(list_connected_clients=lambda *args, **kwargs: {})
    fake_nethsec = types.ModuleType('nethsec')
    fake_nethsec.utils = fake_utils
    fake_nethsec.ovpn = fake_ovpn

    original_argv = sys.argv[:]
    original_euci = sys.modules.get('euci')
    original_nethsec = sys.modules.get('nethsec')
    sys.argv = ['ns.dashboard', 'noop']
    sys.modules['euci'] = fake_euci
    sys.modules['nethsec'] = fake_nethsec

    try:
        loader = SourceFileLoader('ns_dashboard', str(MODULE_PATH))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
    finally:
        sys.argv = original_argv
        if original_euci is None:
            sys.modules.pop('euci', None)
        else:
            sys.modules['euci'] = original_euci
        if original_nethsec is None:
            sys.modules.pop('nethsec', None)
        else:
            sys.modules['nethsec'] = original_nethsec

    return module


class DashboardSummaryTest(unittest.TestCase):
    def test_dashboard_summary_aggregates_initial_dashboard_data(self):
        module = load_module()
        service_calls = []
        counter_calls = []

        module.system_info = lambda: {'hostname': 'fw'}
        module.service_status = lambda service: service_calls.append(service) or {'status': f'{service}-status'}
        module.counter = lambda service: counter_calls.append(service) or {'count': len(service)}
        module.ipsec_tunnels = lambda: {'enabled': 1, 'connected': 0}
        module.ovpn_tunnels = lambda: {'enabled': 2, 'connected': 1}
        module.is_threat_shield_monitoring_enabled = lambda: True

        summary = module.dashboard_summary()

        self.assertEqual(summary['systemInfo'], {'hostname': 'fw'})
        self.assertEqual(
            summary['serviceStatus'],
            {
                'internet': 'internet-status',
                'dns-configured': 'dns-configured-status',
                'mwan': 'mwan-status',
                'netifyd': 'netifyd-status',
                'openvpn_rw': 'openvpn_rw-status',
                'banip': 'banip-status',
                'threat_shield_dns': 'threat_shield_dns-status',
                'dedalo': 'dedalo-status',
            },
        )
        self.assertEqual(
            summary['counters'],
            {
                'hosts': len('hosts'),
                'openvpn_rw': len('openvpn_rw'),
                'threat_shield_ip': len('threat_shield_ip'),
            },
        )
        self.assertEqual(summary['tunnels']['ipsec'], {'enabled': 1, 'connected': 0})
        self.assertEqual(summary['tunnels']['ovpn'], {'enabled': 2, 'connected': 1})
        self.assertEqual(summary['threatShield'], {'monitoringEnabled': True})
        self.assertEqual(
            service_calls,
            [
                'internet',
                'dns-configured',
                'mwan',
                'netifyd',
                'openvpn_rw',
                'banip',
                'threat_shield_dns',
                'dedalo',
            ],
        )
        self.assertEqual(counter_calls, ['hosts', 'openvpn_rw', 'threat_shield_ip'])


if __name__ == '__main__':
    unittest.main()
