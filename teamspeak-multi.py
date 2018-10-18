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


class TeamspeakMulti:
	def config(self):
		config = {
			'bandwidth': [
				'multigraph teamspeak_transfer',
				'graph_order down up',
				'graph_title Teamspeak Bandwidth',
				'graph_args --base 1024',
				'graph_vlabel bytes in (-) / out (+)',
				'graph_category voip',
				'graph_info graph showing the total Teamspeak3 Bandwidth In and Out',

				'down.label received',
				'down.info total amount of bytes received in the last 5 minutes',
				'down.type DERIVE',
				'down.graph no',
				'down.min 0',
				'up.label sent',
				'up.info total amount of bytes sent in the last 5 minutes',
				'up.type DERIVE',
				'up.negative down',
				'up.min 0'
			],
			'filetransfer': [
				'multigraph teamspeak_fttransfer',
				'graph_order ftdown ftup',
				'graph_title Teamspeak File Bandwidth',
				'graph_args --base 1024',
				'graph_vlabel bytes in (-) / out (+)',
				'graph_category voip',
				'graph_info graph showing the Teamspeak3 File Bandwidth In and Out',

				'ftdown.label received',
				'ftdown.info total amount of bytes received for file transfers in the last 5 minutes',
				'ftdown.type DERIVE',
				'ftdown.graph no',
				'ftdown.min 0',
				'ftup.label sent',
				'ftup.info total amount of bytes sent for file transfers in the last 5 minutes',
				'ftup.type DERIVE',
				'ftup.negative ftdown',
				'ftup.min 0'
			],
			'uptime': [
				'multigraph teamspeak_uptime',
				'graph_title TeamSpeak Uptime',
				'graph_args --base 1000 -l 0',
				'graph_scale no',
				'graph_vlabel days',
				'graph_category voip',
				'graph_info graph showing the Teamspeak3 overall uptime',

				'uptime.label uptime in days',
				'uptime.info TeamSpeak Server Uptime',
				'uptime.cdef uptime,86400,/',
				'uptime.min 0',
				'uptime.draw AREA'
			],
			'users': [
				'multigraph teamspeak_usercount',
				'graph_title TeamSpeak User Count',
				'graph_args --base 1000 -l 0',
				'graph_printf %.0lf',
				'graph_vlabel connected users',
				'graph_category voip',
				'graph_info This graph shows the number of connected users on the Teamspeak3 server',

				'user.label last 5 minutes',
				'user.info users connected in the last 5 minutes',
				'user.min 0'
			]
		}

		return config

	def get_data(self, response):
		data = {
			'teamspeak_transfer': [],
			'teamspeak_fttransfer': [],
			'teamspeak_uptime': [],
			'teamspeak_usercount': []
		}

		# transfer
		data['teamspeak_transfer'].append('multigraph teamspeak_transfer')
		data['teamspeak_transfer'].append('down.value %s' % response["connection_bytes_received_total"])
		data['teamspeak_transfer'].append('up.value %s' % response["connection_bytes_sent_total"])

		# fttransfer
		data['teamspeak_fttransfer'].append('multigraph teamspeak_fttransfer')
		data['teamspeak_fttransfer'].append('ftdown.value %s' % response["connection_filetransfer_bytes_received_total"])
		data['teamspeak_fttransfer'].append('ftup.value %s' % response["connection_filetransfer_bytes_sent_total"])

		# uptime
		data['teamspeak_uptime'].append('multigraph teamspeak_uptime')
		data['teamspeak_uptime'].append('uptime.value %s' % response["instance_uptime"])

		# user count
		data['teamspeak_usercount'].append('multigraph teamspeak_usercount')
		data['teamspeak_usercount'].append('user.value %s' % response["virtualservers_total_clients_online"])

		return data

	def run(self):
		# read the configuration from munin environment
		try:
			server = (os.environ['host'], os.environ['port'])
		except KeyError:
			# if connection variables are not set use default
			server = ('localhost', 10011)

		auth = (os.environ['username'], os.environ['password'])

		with ts3.query.TS3Connection(server[0], server[1]) as ts3conn:
			# will raise a TS3QueryError if response code is not 0
			try:
				ts3conn.login(
						client_login_name=auth[0],
						client_login_password=auth[1],
				)
			except ts3.query.TS3QueryError as err:
				print("Login failed:", err.resp.error["msg"])
				exit(1)

			hostinfo = ts3conn.hostinfo().parsed

		result = self.get_data(hostinfo[0])

		for key in result.keys():
			print('\n'.join(result[key]))

	def main(self):
		if (sys.argv.__len__() == 2) and (sys.argv[1] == "config"):
			for key in self.config().keys():
				print('\n'.join(self.config()[key]))
			try:
				if os.environ['MUNIN_CAP_DIRTYCONFIG'] == '1':
					self.run()
			except KeyError:
				pass

		elif (sys.argv.__len__() == 2) and (sys.argv[1] == 'autoconf'):
			# check host if env variables are set
			try:
				if None not in {os.environ['username'], os.environ['password']}:
					print('yes')
			except KeyError:
				print('no env configuration options are missing')
		else:
			self.run()


if __name__ == "__main__":
	TeamspeakMulti().main()
	quit(0)
