How to setup the SimpleCast receiver service.

1. Clone the GIT repo from github to your user running X's home directory (On Raspi this would be /home/pi)
    -- git clone https://github.com/R0NAM1/SimpleCast.git

2. cd into SimpleCast, Install requirements
    -- For debian packages, install the coturn, avahi and python3 package (sudo apt install coturn avahi-daemon python3 portaudio19-dev)
        -- Also install chromium driver for the Selenium driver to work (sudo apt install chromium chromium-chromedriver)

    -- You will probably have to modify the coturn systemd service at /lib/systemd/system/coturn.service to include 'ExecStartPre=/bin/sleep 15' under [Service] so it does not fail on boot
 
    -- For Python Libraries, make a virtual environment (mkdir venv && python3 -m venv venv),
    activate it (source venv/bin/activate), and install from requirements.txt (pip3 install -r requirements.txt).

    -- Install the zeroconf library with pip3 if your not on AARCH64, if so then building the wheel usually takes forever, so just install it from the one I provided in the repo, following your version of python (python3 --version, for example Python 3.11.2). (pip3 install ./zeroconf_aarch64_wheels/zeroconf-0.132.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl)

    --Exit the venv with 'deactivate'.

3. Setup receiver/simpleCastConfig.json however you like, make sure to assign either a static IP or a static leased one!
    -- If this is the first server in a LAN deployment, make the hostname 'simplecastdiscovery' and enable doDnsSdDiscovery for Auto Discovery in clients.
    -- Go into backgrounds and either put in your own images or use a preloaded script

4. Setup avahi to respond to simplecast.local
    -- Copy the provided simplecast-mdns.service to /etc/avahi/services/

5. Setup the systemd service
    -- Open simplecast.service
    -- Adapt WorkingDirectory with the git repo location
    -- Adapt User with the user running X, on a Raspi this would be pi
    -- Adapt ExecStart with the directory that leads to the repo
    -- Copy the file to /etc/systemd/system/
    -- Run 'sudo systemctl daemon-reload', 'sudo systemctl enable simplecast.service' and 'sudo systemctl start simplecast.service'
