# © 2020-2026 Danial Behzadi <dani.behzi@ubuntu.com>
# © 2026 KDE Farsi Community
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
main front file for tractor
"""

import fire

from . import actions, proxy


def main() -> None:
    """
    use fire to manage cli
    """
    fire.Fire(
        {
            "start": actions.start,
            "stop": actions.stop,
            "newid": actions.new_id,
            "restart": actions.restart,
            "set": proxy.proxy_set,
            "unset": proxy.proxy_unset,
            "killtor": actions.kill_tor,
        }
    )


if __name__ == "__main__":
    main()
