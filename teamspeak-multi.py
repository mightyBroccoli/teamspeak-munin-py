#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Plugin to monitor a TeamSpeak Server via telnet
# 	* voice bandwidth
# 	* filetransfer bandwidth
# 	* uptime
# 	* user count
# 	* avg ping
# 	* pktloss statistics

# Parameters understood:
#     config   (required)
#     autoconf (optional - used by munin-config)

# Magic markers - optional - used by installation scripts and
# munin-config:
#
#  #%# family=manual
#  #%# capabilities=autoconf
import ts3
import sys
import os


class TeamspeakMulti:
	def __init__(self):
		# read the configuration from munin environment
		self.host = os.environ.get('host', "localhost")
		self.port = os.environ.get('port', 10011)
		self.id = os.environ.get('id', "1").split(sep=",")

		# config dictionarys
		self.graph = {
			'bandwidth': [
				'multigraph teamspeak_transfer',
				'graph_title Teamspeak Bandwidth',
				'graph_args --base 1024',
				'graph_vlabel bytes in (-) / out (+)',
				'graph_category voip',
				'graph_info graph showing the voice bandwidth in and out'
			],
			'filetransfer': [
				'multigraph teamspeak_fttransfer',
				'graph_title Teamspeak File Bandwidth',
				'graph_args --base 1024',
				'graph_vlabel bytes in (-) / out (+)',
				'graph_category voip',
				'graph_info graph showing the file bandwidth in and out'
			],
			'uptime': [
				'multigraph teamspeak_uptime',
				'graph_title TeamSpeak Uptime',
				'graph_args --base 1000 -l 0',
				'graph_scale no',
				'graph_vlabel days',
				'graph_category voip',
				'graph_info graph showing TeamSpeak3 virtual server uptime'
			],
			'users': [
				'multigraph teamspeak_usercount',
				'graph_title TeamSpeak User Count',
				'graph_args --base 1000 -l 0',
				'graph_printf %.0lf',
				'graph_vlabel connected users',
				'graph_category voip',
				'graph_info graph showing the number of connected users to the server'
			],
			'ping': [
				'multigraph teamspeak_ping',
				'graph_title TeamSpeak Ping',
				'graph_args --base 1000 -l 0',
				'graph_printf %.0lf',
				'graph_vlabel Ping',
				'graph_category voip',
				'graph_info graph showing the average ping'
			],
			'pktloss': [
				'multigraph teamspeak_pktloss',
				'graph_title TeamSpeak packetloss statistics',
				'graph_args --base 1000 -l 0 -u 100 -r',
				'graph_scale no',
				'graph_vlabel packetloss in %',
				'graph_category voip',
				'graph_info graph showing packetloss statistics'
			]
		}
		self.labels = {
			"bandwidth": [
				'down_{sid}.label id_{sid}',
				'down_{sid}.info serverid {sid}\'s amount of bytes received in the last 5 minutes',
				'down_{sid}.type DERIVE',
				'down_{sid}.graph no',
				'down_{sid}.min 0',
				'up_{sid}.label id_{sid}',
				'up_{sid}.info serverid {sid}\'s amount of bytes sent in the last 5 minutes',
				'up_{sid}.type DERIVE',
				'up_{sid}.negative up_{sid}',
				'up_{sid}.min 0'
			],
			"filetransfer": [
				'ftdown_{sid}.label id_{sid}',
				'ftdown_{sid}.info serverid {sid}\'s amount of filetransfer bytes received in the last 5 minutes',
				'ftdown_{sid}.type DERIVE',
				'ftdown_{sid}.graph no',
				'ftdown_{sid}.min 0',
				'ftup_{sid}.label id_{sid}',
				'ftup_{sid}.info serverid {sid}\'s amount of filetransfer bytes sent in the last 5 minutes',
				'ftup_{sid}.type DERIVE',
				'ftup_{sid}.negative ftup_{sid}',
				'ftup_{sid}.min 0'
			],
			"uptime": [
				'uptime_{sid}.label id_{sid}',
				'uptime_{sid}.info serverid {sid}\'s uptime',
				'uptime_{sid}.cdef uptime_{sid},86400,/',
				'uptime_{sid}.min 0',
				'uptime_{sid}.draw AREA'
			],
			"users": [
				'user_{sid}.label id_{sid} users',
				'user_{sid}.info users connected to serverid_{sid} in the last 5 minutes',
				'user_{sid}.min 0',
				'queryuser_{sid}.label id_{sid} queryusers',
				'queryuser_{sid}.info queryusers connected to serverid_{sid} in the last 5 minutes',
				'queryuser_{sid}.min 0',
			],
			"ping": [
				'ping_{sid}.label id_{sid}',
				'ping_{sid}.info average ping of users connected to serverid_{sid}',
				'ping_{sid}.min 0'
			],
			"pktloss": [
				'speech_{sid}.label id_{sid} speech',
				'speech_{sid}.info serverid {sid}\'s average speech packetloss',
				'speech_{sid}.min 0',
				'speech_{sid}.draw STACK',
				'keepalive_{sid}.label id_{sid} keepalive',
				'keepalive_{sid}.info serverid {sid}\'s average keepalive packetloss',
				'keepalive_{sid}.min 0',
				'keepalive_{sid}.draw STACK',
				'control_{sid}.label id_{sid} control',
				'control_{sid}.info serverid {sid}\'s average control packetloss',
				'control_{sid}.min 0',
				'control_{sid}.draw STACK',
				'total_{sid}.label id_{sid} total',
				'total_{sid}.info serverid {sid}\'s combined average packetloss',
				'total_{sid}.min 0',
				'total_{sid}.draw STACK'
			]
		}

		# result dictionary
		self.data = {
			'teamspeak_transfer': ['multigraph teamspeak_transfer'],
			'teamspeak_fttransfer': ['multigraph teamspeak_fttransfer'],
			'teamspeak_uptime': ['multigraph teamspeak_uptime'],
			'teamspeak_user': ['multigraph teamspeak_usercount'],
			'teamspeak_ping': ['multigraph teamspeak_ping'],
			'teamspeak_pktloss': ['multigraph teamspeak_pktloss']
		}

	def config(self):
		# for every key in self.graph print out the config parameter
		for key in self.graph:
			print('\n'.join(self.graph[key]))

			# in addition to the general config add specific field values
			# fielname_$sid.option string
			for sid in self.id:
				if sid.isdigit():
					print('\n'.join(self.labels[key]).replace("{sid}", str(sid)))

	def get_data(self, sid, response):
		# use the data dictionary to accumulate all results together
		data = self.data

		# transfer
		data['teamspeak_transfer'].append('down_%s.value %s' % (sid, response["connection_bytes_received_total"]))
		data['teamspeak_transfer'].append('up_%s.value %s' % (sid, response["connection_bytes_sent_total"]))

		# fttransfer
		data['teamspeak_fttransfer'].append('ftdown_%s.value %s' % (sid, response["connection_filetransfer_bytes_received_total"]))
		data['teamspeak_fttransfer'].append('ftup_%s.value %s' % (sid, response["connection_filetransfer_bytes_sent_total"]))

		# uptime
		data['teamspeak_uptime'].append('uptime_%s.value %s' % (sid, response["virtualserver_uptime"]))

		# user connections
		clientcount = int(response["virtualserver_clientsonline"]) - int(response["virtualserver_queryclientsonline"])
		data['teamspeak_user'].append('user_%s.value %s' % (sid, clientcount))
		data['teamspeak_user'].append('queryuser_%s.value %s' % (sid, response["virtualserver_queryclientsonline"]))

		# avg ping
		data['teamspeak_ping'].append('ping_%s.value %s' % (sid, response["virtualserver_total_ping"]))

		# packetloss statistics
		data['teamspeak_pktloss'].append('speech_%s.value %s' % (sid, response["virtualserver_total_packetloss_speech"]))
		data['teamspeak_pktloss'].append('keepalive_%s.value %s' % (sid, response["virtualserver_total_packetloss_keepalive"]))
		data['teamspeak_pktloss'].append('control_%s.value %s' % (sid, response["virtualserver_total_packetloss_control"]))
		data['teamspeak_pktloss'].append('total_%s.value %s' % (sid, response["virtualserver_total_packetloss_total"]))

	def run(self):
		with ts3.query.TS3Connection(self.host, self.port) as ts3conn:
			# will raise a TS3QueryError if response code is not 0
			try:
				ts3conn.login(client_login_name=os.environ['username'], client_login_password=os.environ['password'])

				for sid in self.id:
					if sid.isdigit():
						ts3conn.use(sid=sid)
						info = ts3conn.serverinfo().parsed
						self.get_data(sid, info[0])

				# for key in results print every entry in dict
				[print('\n'.join(self.data[key])) for key in self.data.keys()]

			except (ts3.query.TS3QueryError, KeyError) as err:
				print("Login failed:", err.resp.error["msg"])
				exit(1)

	def main(self):
		# check if any argument is given 
		if sys.argv.__len__() >= 2:
			# check if first argument is config or autoconf if not fetch data
			if sys.argv[1] == "config":
				# output config parameter
				self.config()
				if os.environ.get('MUNIN_CAP_DIRTYCONFIG') == '1':
					self.run()
			elif sys.argv[1] == 'autoconf':
				if None in [os.environ.get('username'), os.environ.get('password')]:
					print('env variables are missing')
				else:
					print('yes')
		else:
			self.run()


if __name__ == "__main__":
	TeamspeakMulti().main()
