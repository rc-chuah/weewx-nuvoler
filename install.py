# installer for nuvoler
# Copyright © 2026 RC Chuah (Based on weewx-windy by Matthew Wall and Jacques Terrettaz)
# Distributed under the terms of the GNU General Public License (GPLv3)

from weecfg.extension import ExtensionInstaller

def loader():
    return NuvolerInstaller()

class NuvolerInstaller(ExtensionInstaller):
    def __init__(self):
        super(NuvolerInstaller, self).__init__(
            version="0.1",
            name='nuvoler',
            description='Upload weather data to Nuvoler.',
            author="RC Chuah (Based on weewx-windy by Matthew Wall and Jacques Terrettaz)",
            author_email="44928288+rc-chuah@users.noreply.github.com",
            restful_services='user.nuvoler.Nuvoler',
            config={
                'StdRESTful': {
                    'Nuvoler': {
                        'station_id': 'YOUR_STATION_ID_HERE',
                        'station_pass': 'YOUR_STATION_PASSWORD_HERE'
                    }
                }
            },
            files=[('bin/user', ['bin/user/nuvoler.py'])]
        )
