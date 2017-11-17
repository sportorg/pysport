import os
import json

from sportorg import config


with open(config.base_dir('versioninfo.json'), 'w') as _f:
    json.dump(config.VERSION_INFO, _f, indent=4)

# https://github.com/josephspurrier/goversioninfo
os.system('{} -icon={}'.format(config.base_dir('goversioninfo'), config.ICON))

# golang
os.system('go build -ldflags="-H windowsgui" -o {}.exe'.format(config.NAME))
