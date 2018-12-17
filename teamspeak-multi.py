#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Plugin to monitor a TeamSpeak Server via telnet
# 	* general bandwidth
# 	* filetransfer bandwidth
# 	* uptime
# 	* user count
#
# Parameters understood:
#     config   (required)
#     autoconf (optional - used by munin-config)
#
# Magic markers - optional - used by installation scripts and
# munin-config:
#
#  #%# family=manual
#  #%# capabilities=autoconf
import ts3
import sys
import os
import re


class TeamspeakMulti:
	def __init__(self):
		# read the configuration from munin environment
		self.host = os.environ.get('host', "localhost")
		self.port = os.environ.get('port', 10011)
		self.id = os.environ.get('id', "1").split(sep=",")

		self.names = dict()
		self.graph = {
			'bandwidth': [
				'multigraph teamspeak_transfer',
				'graph_title Teamspeak Bandwidth',
				'graph_args --base 1024',
				'graph_vlabel bytes in (-) / out (+)',
				'graph_category voip',
				'graph_info graph showing the total Teamspeak3 Bandwidth In and Out'
			],
			'filetransfer': [
				'multigraph teamspeak_fttransfer',
				'graph_title Teamspeak File Bandwidth',
				'graph_args --base 1024',
				'graph_vlabel bytes in (-) / out (+)',
				'graph_category voip',
				'graph_info graph showing the Teamspeak3 File Bandwidth In and Out'
			],
			'uptime': [
				'multigraph teamspeak_uptime',
				'graph_title TeamSpeak Uptime',
				'graph_args --base 1000 -l 0',
				'graph_scale no',
				'graph_vlabel days',
				'graph_category voip',
				'graph_info graph showing the Teamspeak3 overall uptime'
			],
			'users': [
				'multigraph teamspeak_usercount',
				'graph_title TeamSpeak User Count',
				'graph_args --base 1000 -l 0',
				'graph_printf %.0lf',
				'graph_vlabel connected users',
				'graph_category voip',
				'graph_info This graph shows the number of connected users on the Teamspeak3 server'
			],
			'connection': [
				'multigraph teamspeak_connection',
				'graph_title TeamSpeak connection statistics',
				'graph_args --base 1000 -l 0',
				'graph_printf %.0lf',
				'graph_vlabel connected users',
				'graph_category voip',
				'graph_info graph showing general connection statistics'
			]
		}
		self.labels = {
			"bandwidth": [
				'down_%d.label %s',
				'down_%d.info total amount of bytes received in the last 5 minutes',
				'down_%d.type DERIVE',
				'down_%d.graph no',
				'down_%d.min 0',
				'up_%d.label %s',
				'up_%d.info total amount of bytes sent in the last 5 minutes',
				'up_%d.type DERIVE',
				'up_%d.negative down',
				'up_%d.min 0'
			],
			"filetransfer": [
				'ftdown_%d.label %s',
				'ftdown_%d.info file transfer bytes received in the last 5 minutes',
				'ftdown_%d.type DERIVE',
				'ftdown_%d.graph no',
				'ftdown_%d.min 0',
				'ftup_%d.label %s',
				'ftup_%d.info file transfer bytes sent in the last 5 minutes',
				'ftup_%d.type DERIVE',
				'ftup_%d.negative ftdown',
				'ftup_%d.min 0'
			],
			"uptime": [
				'uptime_%d.label %s uptime',
				'uptime_%d.info %s server uptime',
				'uptime_%d.cdef uptime,86400,/',
				'uptime_%d.min 0',
				'uptime_%d.draw AREA'
			],
			"users": [
				'user_%d.label %s usercount',
				'user_%d.info users connected in the last 5 minutes',
				'user_%d.min 0',
				'queryuser_%d.label %s queryuserscount',
				'queryuser_%d.info queryusers connected in the last 5 minutes',
				'queryuser_%d.min 0',
				'ping_%d.label %s avg. ping',
				'ping_%d.info average ping of users connected to %s',
				'ping_%d.min 0',
				'pktloss_%d.label %s avg. packetloss',
				'pktloss_%d.info average packetloss of users connected to %s',
				'pktloss_%d.min 0'
			],
			"connection": [
				'ping_%d.label %s avg. ping',
				'ping_%d.info average ping of users connected to %s',
				'ping_%d.min 0',
				'pktloss_%d.label %s avg. packetloss',
				'pktloss_%d.info average packetloss of users connected to %s',
				'pktloss_%d.min 0'
			]
		}

	def config(self):
		# todo comment
		self.run("config")

		for key in self.graph:
			print('\n'.join(self.graph[key]))

			for sid in self.id:
				if sid.isdigit():
					name = self.names[sid]
					print('\n'.join(self.labels[key]).replace("%d", str(sid)).replace("%s", str(name)))

	def get_data(self,sid, response):
		data = {
			'teamspeak_transfer': [],
			'teamspeak_fttransfer': [],
			'teamspeak_uptime': [],
			'teamspeak_usercount': [],
			'teamspeak_connection': []
		}

		# transfer
		data['teamspeak_transfer'].append('multigraph teamspeak_transfer')
		data['teamspeak_transfer'].append('down_%s.value %s' % (sid, response["connection_bytes_received_total"]))
		data['teamspeak_transfer'].append('up_%s.value %s' % (sid, response["connection_bytes_sent_total"]))

		# fttransfer
		data['teamspeak_fttransfer'].append('multigraph teamspeak_fttransfer')
		data['teamspeak_fttransfer'].append('ftdown_%s.value %s' % (sid, response["connection_filetransfer_bytes_received_total"]))
		data['teamspeak_fttransfer'].append('ftup_%s.value %s' % (sid, response["connection_filetransfer_bytes_sent_total"]))

		# uptime
		data['teamspeak_uptime'].append('multigraph teamspeak_uptime')
		data['teamspeak_uptime'].append('uptime_%s.value %s' % (sid, response["virtualserver_uptime"]))

		# user connections
		clientcount = int(response["virtualserver_clientsonline"]) - int(response["virtualserver_queryclientsonline"])

		data['teamspeak_usercount'].append('multigraph teamspeak_usercount')
		data['teamspeak_usercount'].append('user_%s.value %s' % (sid, clientcount))
		data['teamspeak_usercount'].append('queryuser_%s.value %s' % (sid, response["virtualserver_queryclientsonline"]))

		# connection statistics
		data['teamspeak_connection'].append('multigraph teamspeak_connection')
		data['teamspeak_connection'].append('ping_%s.value %s' % (sid, response["virtualserver_total_ping"]))
		data['teamspeak_connection'].append('pktloss_%s.value %s' % (sid, response["virtualserver_total_packetloss_total"]))

		# for key in results print every entry in dict
		[print('\n'.join(data[key])) for key in data.keys()]

	def clean_fieldname(self, text):
		return re.sub(r"(^[^A-Za-z_]|[^A-Za-z0-9_])", "", text)

	def get_names(self, response):
		# todo comment
		for server in response:
			self.names[str(server["virtualserver_id"])] = self.clean_fieldname(server["virtualserver_name"])

	def run(self, arg=None):
		with ts3.query.TS3Connection(self.host, self.port) as ts3conn:
			# will raise a TS3QueryError if response code is not 0
			try:
				ts3conn.login(client_login_name=os.environ['username'], client_login_password=os.environ['password'])

				if arg == "config":
					serverlist = ts3conn.serverlist().parsed
					self.get_names(serverlist)
					return

				for sid in self.id:
					if sid.isdigit():
						ts3conn.use(sid=sid)
						info = ts3conn.serverinfo().parsed
						self.get_data(sid, info[0])

			except (ts3.query.TS3QueryError, KeyError) as err:
				print("Login failed:", err.resp.error["msg"])
				exit(1)

	def main(self):
		# check if any argument is given
		if sys.argv.__len__() >= 2:
			# check if first argument is config or autoconf if not fetch data
			if sys.argv[1] == "config":
				# add comment
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
