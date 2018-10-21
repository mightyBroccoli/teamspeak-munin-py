# TeamSpeak 3 Munin Multigraph Plugin
This repository features a basic [TeamSpeak3](https://www.teamspeak.de/) Munin Plugin, which gathers information from the TeamSpeak Telnet.

There are drawbacks to using a multigraph plugin which can be read up here : [Munin-Monitoring.org](http://guide.munin-monitoring.org/en/latest/plugin/multigraphing.html)

## install
To use these plugin properly some configuration parameters are required to be present inside the plugin-config `/etc/munin/plugin-config.d/munin-node`.
```
[teamspeak*]
username = username
password = password
# host and port are not required if the default values are true for your setup
host = localhost
port = 10011
```
To install these plugins, you just have to symlink those plugins you would like to activate to the munin plugin directory eg. `/etc/munin/plugins/`. Or if you want to use the multigraph plugin only symlink that one the the munin plugin directory.

After this has been done the munin-node needs to be restarted to facilitate the new plugins.
`systemctl restart munin-node`

##### is everything working correctly
To check if the plugin is working correctly it is necessary to first instruct the capability multigraph before the `list` instruction.
```
telnet localhost 4949 # localhost or IP the munin-node
cap multigraph
list
fetch teamspeak-munin.py
```
The `list` command will return a list of all plugins currently active. This list should feature the newly activated 
teamspeak plugin.
The `fetch` commands will run the script and return the gathered values. As long as none of them are NaN everything works as expected.

### uninstall
To remove the plugins from munin remove all symlinked plugins from the directory and restart the node.
