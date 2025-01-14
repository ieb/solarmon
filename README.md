Solarmon
----
A simple Python Script for reading Growatt PV Inverter Modbus RS485 RTU Protocol and storing into InfluxDB

Forked from original and upgraded to v120 of the Growatt Modbus RTU registers. Tested with a Growatt 4200 TL XE 1 phase 2mpp inverter, shipped in early 2022. 

[Protocol Documentation](docs/README.md)

How to use
----
- Some hardware running a Linux based OS with Python 3 (eg. Raspberry Pi)
- Connect your Linux based OS to the RS485 port on the inverter via a RS485 to USB cable
- [Install InfluxDB](https://www.influxdata.com/)
- Copy `solarmon.cfg.example` to `solarmon.cfg` and modify the config values to your setup as needed
- Run `pip install -r requirements.txt`
- Run `python solarmon.py` in a screen (or you could setup a service if that is your preference)
- [Install Grafana](https://grafana.com/)
- Go to http://localhost:3000/dashboard/import or equivalent for where you installed Grafana and import `grafana/dashboard.json`

![Inverter Grafana Dashboard](grafana/dashboard.png)


Reading from Multiple Units
----
To read from multiple units add a new section to the `solarmon.cfg` config with the unit's id and the measurement name to store the units data in influxdb
```ini
[inverters.<name>]
unit = <id>
measurement = <mesurement>
```
Example:
```ini
[inverters.unit2]
unit = 2
measurement = inverter2
```

To view the data using a Grafana dashboard simply import the template like described above in "How to use" and then change the measurement variable at the top of the page to match what you put in the config, in the example that is 'inverter2'. 

Systemd Service
---
- Copy `solarmon.service` to `/etc/systemd/system`
- Modify the `WorkingDirectory` and `User` to suit your setup.
- Run `systemctl start solarmon` to start the service.
- Run `systemctl status solarmon` and ensure that the service is running correctly.
- Run `systemctl enable solarmon` to make the service automatically start when the system does.


Additonal Monitors
---

- Gateway
- Meters
- Set Export Limits

Gateway
---

With Modbus its not possible to have 2 controllers on the same physical bus. Gateway sniffs an Modbus bus capturing the conversation between a controler and device and storing the values of the registers in a byte[] which can then be queried and used. This is of use when a meter is connected to a inverter with the inverter operating as the controller, hence only the inverter can query the meter for registers. 

Meters
---

Queries meters and sends the data to influx. Is currently setup for SDM230 protocol meters sending all available input registers to influx. Accompanied by a systemd service to run as a service.

Set Export Limits
---

Utility script to query Growatt holding registers. This also sets the export limit and export fail limit on the inverter assumign that the inverter is not locked. It has been tested and works on a Growatt 4200 LT XE believed to have been manufactured in 2021. The register locations do change, but if this reports meaningful values when querying there is a good chance the registers on a different unit are the same. It will operate in dry run mode making no changes unless invoked as

```
python setExportLimit.py set
```






