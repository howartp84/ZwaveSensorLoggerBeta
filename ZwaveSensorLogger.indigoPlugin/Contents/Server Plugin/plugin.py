#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2016, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

#Thanks to Krisstian for teaching me how to join() and use xrange() in one-liner commands!

import indigo

import os
import sys

import time

import fnmatch

#This is a test

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

########################################
# Tiny function to convert a list of integers (bytes in this case) to a
# hexidecimal string for pretty logging.
def convertListToHexStr(byteList):
	return ' '.join(["%02X" % byte for byte in byteList])

def convertListToStr(byteList):
	return ' '.join(["%02X" % byte for byte in byteList])

################################################################################
class Plugin(indigo.PluginBase):
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = pluginPrefs.get("showDebugInfo", False)

		self.powerIDs = list()
		self.tempIDs = list()

		self.zedFromDev = dict()
		self.zedFromNode = dict()
		self.devFromZed = dict()
		self.devFromNode = dict()
		self.nodeFromZed = dict()
		self.nodeFromDev = dict()

	########################################
	def startup(self):
		self.debugLog(u"startup called")
		indigo.zwave.subscribeToIncoming()
		#indigo.zwave.subscribeToOutgoing()

	def shutdown(self):
		self.debugLog(u"shutdown called")

	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		# Since the dialog closed we want to set the debug flag - if you don't directly use
		# a plugin's properties (and for debugLog we don't) you'll want to translate it to
		# the appropriate stuff here.
		if not userCancelled:
			self.debug = valuesDict.get("showDebugInfo", False)
			if self.debug:
				indigo.server.log("Debug logging enabled")
			else:
				indigo.server.log("Debug logging disabled")

	def deviceStartComm(self, dev):
		dev.stateListOrDisplayStateIdChanged()
		if (dev.deviceTypeId == "zpower"):
			devID = dev.id																							#devID is the Indigo ID of my dummy device
			zedID = dev.ownerProps['deviceId']													#zedID is the Indigo ID of the actual ZWave device
			nodeID = indigo.devices[int(zedID)].ownerProps['address']		#nodeID is the ZWave Node ID

			self.zedFromDev[int(devID)] = int(zedID)
			self.zedFromNode[int(nodeID)] = int(zedID)
			self.devFromZed[int(zedID)] = int(devID)
			self.devFromNode[int(nodeID)] = int(devID)
			self.nodeFromZed[int(zedID)] = int(nodeID)
			self.nodeFromDev[int(devID)] = int(nodeID)

			self.powerIDs.append(nodeID)

		if (dev.deviceTypeId == "ztemp"):
			devID = dev.id																							#devID is the Indigo ID of my dummy device
			zedID = dev.ownerProps['deviceId']													#zedID is the Indigo ID of the actual ZWave device
			nodeID = indigo.devices[int(zedID)].ownerProps['address']		#nodeID is the ZWave Node ID

			self.zedFromDev[int(devID)] = int(zedID)
			self.zedFromNode[int(nodeID)] = int(zedID)
			self.devFromZed[int(zedID)] = int(devID)
			self.devFromNode[int(nodeID)] = int(devID)
			self.nodeFromZed[int(zedID)] = int(nodeID)
			self.nodeFromDev[int(devID)] = int(nodeID)

			self.tempIDs.append(nodeID)

	def deviceStopComm(self, dev):
		if (dev.deviceTypeId == "zpower"):
			devID = dev.id
			zedID = dev.ownerProps['deviceId']
			nodeID = indigo.devices[int(zedID)].ownerProps['address']

			self.zedFromDev.pop(int(devID),None)
			self.zedFromNode.pop(int(nodeID),None)
			self.devFromZed.pop(int(zedID),None)
			self.devFromNode.pop(int(nodeID),None)
			self.nodeFromZed.pop(int(zedID),None)
			self.nodeFromDev.pop(int(devID),None)

			self.powerIDs.remove(nodeID)

		if (dev.deviceTypeId == "ztemp"):
			devID = dev.id
			zedID = dev.ownerProps['deviceId']
			nodeID = indigo.devices[int(zedID)].ownerProps['address']

			self.zedFromDev.pop(int(devID),None)
			self.zedFromNode.pop(int(nodeID),None)
			self.devFromZed.pop(int(zedID),None)
			self.devFromNode.pop(int(nodeID),None)
			self.nodeFromZed.pop(int(zedID),None)
			self.nodeFromDev.pop(int(devID),None)

			self.tempIDs.remove(nodeID)


##########################################################################################################################################################

	def zwaveCommandReceived(self, cmd):
		byteList = cmd['bytes']			# List of the raw bytes just received.
		byteListStr = convertListToHexStr(byteList)
		nodeId = cmd['nodeId']			# Can be None!
		endpoint = cmd['endpoint']		# Often will be None!

		bytes = byteListStr.split()
		nodeId = int(bytes[5],16)

		if (int(bytes[5],16)) in self.powerIDs: #Power Devices
			#self.debugLog(u"Raw command received (Node %s): %s" % ((int(bytes[5],16)),(byteListStr)))

			socketMap = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6} #socketMap[endPoint] = SocketNo

			dev=indigo.devices[self.devFromNode[nodeId]]

			if (bytes[7] == "32") and (bytes[8] == "02"): #ENERGY REPORT (Base Device)
				if (len(bytes) <> 99):
					self.debugLog(u"-----")
					#self.debugLog(u"Power/Energy report received:")
					self.debugLog(u"Raw command: %s" % (byteListStr))
					#self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
					if (endpoint <> None):
						self.debugLog(u"Endpoint[Node]:  " + str(endpoint))

					bmask = bin(int(bytes[10],16))
					#self.debugLog(str(bmask) + ": " + str(bytes[10]))
					bstr = '00000000' + bmask[2:]
					bstr = bstr[-8:]
					bmdp, bmsc, bmlen = bstr[0:3], bstr[3:5], bstr[5:8]
					#self.debugLog(u"DP: %s, Scale: %s, ByteLength: %s" % ((bmdp,bmsc,bmlen)))
					bmdp = int(bmdp,2)
					bmsc = int(bmsc,2)
					bmlen = int(bmlen,2)
					self.debugLog(u"Bitmask: %s, DP: %s, Scale: %s, ByteLength: %s" % ((bytes[10],bmdp,bmsc,bmlen)))

					if (bmlen == 1):
						value = int(bytes[11],16)
					elif (bmlen == 2):
						value = int(bytes[11] + bytes[12],16)
					elif (bmlen == 4):
						value = int(bytes[11] + bytes[12] + bytes[13] + bytes[14],16)

					value = float(value) / (10**bmdp) # Divide by 10^2 (100) or 10^3 (1000) etc

					if (bmsc == 0): #kWh
						self.debugLog(u"Energy Reported: " + str(value) + " kWh")
						stateid = "totalenergyrep"
					elif (bmsc == 1): #kVAh
						self.debugLog(u"Energy Reported: " + str(value) + " kVAh")
						stateid = "totalenergyrep"
					elif (bmsc == 2): #w
						self.debugLog(u"Power Reported: " + str(value) + " w")
						stateid = "totalpowerrep"

					dev.updateStateOnServer(stateid, value)

					#if (bytes[10] == "74"): #3DP, Watts, 4bytes
						#fullpower = int(bytes[11] + bytes[12] + bytes[13] + bytes[14],16)
						#decpower = float(fullpower)/1000
						#self.debugLog(u"Total Power Reported: " + str(fullpower) + " (" + str(decpower) + ") watts")
						#dev.updateStateOnServer(stateid, decpower)
					#elif (bytes[10] == "34"): #1DP, Watts, 4bytes
						#fullpower = int(bytes[11] + bytes[12] + bytes[13] + bytes[14],16)
						#decpower = float(fullpower)/10
						#self.debugLog(u"Total Power Reported: " + str(fullpower) + " (" + str(decpower) + ") watts")
						#dev.updateStateOnServer(stateid, decpower)

				else: #Invalid size
					self.debugLog("Incorrect packet size - ignoring")


			if (bytes[7] == "60") and (bytes[8] == "0D") and (bytes[11] == "32") and (bytes[12] == "02"): #MULTI_CHANNEL ENERGY
				if (len(bytes) <> 99):
					self.debugLog(u"-----")
					#self.debugLog(u"Power/Energy report received:")
					self.debugLog(u"Raw command: %s" % (byteListStr))
					#self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
					self.debugLog(u"Endpoint[Raw]:  %s" % (int(bytes[9],16)))
					if (endpoint <> None):
						self.debugLog(u"Endpoint[Node]:  " + str(endpoint))


					bmask = bin(int(bytes[14],16))
					#self.debugLog(str(bmask) + ": " + str(bytes[10]))
					bstr = '00000000' + bmask[2:]
					bstr = bstr[-8:]
					bmdp, bmsc, bmlen = bstr[0:3], bstr[3:5], bstr[5:8]
					#self.debugLog(u"DP: %s, Scale: %s, ByteLength: %s" % ((bmdp,bmsc,bmlen)))
					bmdp = int(bmdp,2)
					bmsc = int(bmsc,2)
					bmlen = int(bmlen,2)
					self.debugLog(u"Bitmask: %s, DP: %s, Scale: %s, ByteLength: %s" % ((bytes[14],bmdp,bmsc,bmlen)))

					if (bmlen == 1):
						value = int(bytes[15],16)
					elif (bmlen == 2):
						value = int(bytes[15] + bytes[16],16)
					elif (bmlen == 4):
						value = int(bytes[15] + bytes[16] + bytes[17] + bytes[18],16)

					value = float(value) / (10**bmdp) # Divide by 10^2 (100) or 10^3 (1000) etc

					if (bmsc == 0): #kWh
						self.debugLog(u"Endpoint Energy Reported: " + str(value) + " kWh")
						stateid = "socket" + str(socketMap[int(bytes[9],16)]) + "energy"
					elif (bmsc == 2): #w
						self.debugLog(u"Endpoint Power Reported: " + str(value) + " w")
						stateid = "socket" + str(socketMap[int(bytes[9],16)]) + "power"

					dev.updateStateOnServer(stateid, value)
					stampid = "socket" + str(socketMap[int(bytes[9],16)]) + "stamp"
					timestamp = time.strftime("%d %b %y %H:%M:%S")
					dev.updateStateOnServer(stampid, str(timestamp))



					#if (bytes[14] == "74"): #3DP, Watts, 4bytes
						#fullpower = int(bytes[15] + bytes[16] + bytes[17] + bytes[18],16)
						#decpower = float(fullpower)/1000
						#self.debugLog(u"Power: " + str(fullpower) + " (" + str(decpower) + ") watts")
						#dev.updateStateOnServer(stateid, decpower)
					#elif (bytes[14] == "34"): #1DP, Watts, 4bytes
						#fullpower = int(bytes[15] + bytes[16] + bytes[17] + bytes[18],16)
						#decpower = float(fullpower)/10
						#self.debugLog(u"Power: " + str(fullpower) + " (" + str(decpower) + ") watts")
						#dev.updateStateOnServer(stateid, decpower)

					self.debugLog(u"")

					tenergy = float(dev.states["socket1energy"]) + float(dev.states["socket2energy"]) + float(dev.states["socket3energy"]) + float(dev.states["socket4energy"]) + float(dev.states["socket5energy"]) + float(dev.states["socket6energy"]) + float(dev.states["socket7energy"]) + float(dev.states["socket8energy"])
					self.debugLog(u"Total Energy Calculated: " + str(tenergy) + " kWh")
					dev.updateStateOnServer("totalenergycalc",tenergy)

					tpower = float(dev.states["socket1power"]) + float(dev.states["socket2power"]) + float(dev.states["socket3power"]) + float(dev.states["socket4power"]) + float(dev.states["socket5power"]) + float(dev.states["socket6power"]) + float(dev.states["socket7power"]) + float(dev.states["socket8power"])
					self.debugLog(u"Total Power Calculated: " + str(tpower) + " w")
					dev.updateStateOnServer("totalpowercalc",tpower)

				else: #Incorrect size
					self.debugLog("Incorrect packet size - ignoring")


##########################################################################################################################################################


		if (int(bytes[5],16)) in self.tempIDs: #Temperature Devices
			#self.debugLog(u"Raw command received (Node %s): %s" % ((int(bytes[5],16)),(byteListStr)))

			socketMap = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6} #socketMap[endPoint] = SocketNo

			dev=indigo.devices[self.devFromNode[nodeId]]

			if (bytes[7] == "31") and (bytes[8] == "05") and (bytes[9] == "05"): #HUMIDITY SENSOR REPORT (Base Device)
				#self.debugLog(u"-----")
				#self.debugLog(u"Humidity report received:")
				#self.debugLog(u"Raw command: %s" % (byteListStr))
				#self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
				#self.debugLog(u"Endpoint:  Base")

				bmask = bin(int(bytes[10],16))
				#self.debugLog(str(bmask) + ": " + str(bytes[10]))
				bstr = '00000000' + bmask[2:]
				bstr = bstr[-8:]
				bmdp, bmsc, bmlen = bstr[0:3], bstr[3:5], bstr[5:8]
				#self.debugLog(u"DP: %s, Scale: %s, ByteLength: %s" % ((bmdp,bmsc,bmlen)))
				bmdp = int(bmdp,2)
				bmsc = int(bmsc,2)
				bmlen = int(bmlen,2)
				self.debugLog(u"Bitmask: %s, DP: %s, Scale: %s, ByteLength: %s" % ((bytes[14],bmdp,bmsc,bmlen)))

				if (bmlen == 1):
					value = int(bytes[11],16)
				elif (bmlen == 2):
					value = int(bytes[11] + bytes[12],16)
				elif (bmlen == 4):
					value = int(bytes[11] + bytes[12] + bytes[13] + bytes[14],16)

				value = float(value) / (10**bmdp) # Divide by 10^2 (100) or 10^3 (1000) etc

				if (bmsc == 0): # %age humidity
					self.debugLog(u"Humidity Reported (Node " + str(int(bytes[5],16)) + " Endpoint " + str(endpoint) + "): " + str(dechumid) + "%")
					stateid = "humidity"
				elif (bmsc == 1): #just a value
					self.debugLog(u"Humidity Reported (Node " + str(int(bytes[5],16)) + " Endpoint " + str(endpoint) + "): " + str(dechumid))
					stateid = "humidity"

				dev.updateStateOnServer(stateid, value)
				stampid = stateid + "stamp"
				timestamp = time.strftime("%d %b %y %H:%M:%S")
				dev.updateStateOnServer(stampid, str(timestamp))



				#self.debugLog(u"Format:    %s" % (bytes[10]))
				#stateid = "humidity"
				#self.debugLog(u"State:     %s" % (stateid))
				#if (bytes[10] == "42"): #2DP, %age, 2bytes
					#humid = int(bytes[11] + bytes[12],16)
					#dechumid = float(humid)/100
					#self.debugLog(u"Humidity Reported (Node " + str(int(bytes[5],16)) + " Endpoint " + str(endpoint) + "): " + str(dechumid) + "%")
					#dev.updateStateOnServer(stateid, dechumid)
					#stampid = stateid + "stamp"
					#timestamp = time.strftime("%s %b %y %H:%M:%S")
					#dev.updateStateOnServer(stampid, str(timestamp))

			elif (bytes[7] == "31") and (bytes[8] == "05") and (bytes[9] == "01"): #TEMPERATURE SENSOR REPORT (Base Device)
				#self.debugLog(u"-----")
				#self.debugLog(u"Base temperature report received:")
				#self.debugLog(u"Raw command: %s" % (byteListStr))
				##self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
				#self.debugLog(u"Endpoint:  Base")


				bmask = bin(int(bytes[10],16))
				#self.debugLog(str(bmask) + ": " + str(bytes[10]))
				bstr = '00000000' + bmask[2:]
				bstr = bstr[-8:]
				bmdp, bmsc, bmlen = bstr[0:3], bstr[3:5], bstr[5:8]
				#self.debugLog(u"DP: %s, Scale: %s, ByteLength: %s" % ((bmdp,bmsc,bmlen)))
				bmdp = int(bmdp,2)
				bmsc = int(bmsc,2)
				bmlen = int(bmlen,2)
				self.debugLog(u"Bitmask: %s, DP: %s, Scale: %s, ByteLength: %s" % ((bytes[14],bmdp,bmsc,bmlen)))

				if (bmlen == 1):
					value = int(bytes[11],16)
				elif (bmlen == 2):
					value = int(bytes[11] + bytes[12],16)
				elif (bmlen == 4):
					value = int(bytes[11] + bytes[12] + bytes[13] + bytes[14],16)

				value = float(value) / (10**bmdp) # Divide by 10^2 (100) or 10^3 (1000) etc

				if (bmsc == 0): # celsius
					uivalue = value + " °c"
					self.debugLog(u"Temperature Reported (Node " + str(int(bytes[5],16)) + " Endpoint " + str(endpoint) + "): " + str(dectemp) + " celsius")
					stateid = "temp" + str(endpoint)
					if (endpoint == None):
						stateid = "temp1"
				elif (bmsc == 1): #farenheit
					uivalue = value + " °f"
					self.debugLog(u"Temperature Reported (Node " + str(int(bytes[5],16)) + " Endpoint " + str(endpoint) + "): " + str(dectemp) + " fahrenheit")
					stateid = "temp" + str(endpoint)
					if (endpoint == None):
						stateid = "temp1"

				dev.updateStateOnServer(stateid, value, uiValue=uivalue)
				stampid = stateid + "stamp"
				timestamp = time.strftime("%d %b %y %H:%M:%S")
				dev.updateStateOnServer(stampid, str(timestamp))





				#stateid = "temp" + str(endpoint)
				#if (endpoint == None):
					#stateid = "temp1"
				#self.debugLog(u"State:     %s" % (stateid))
				#if (bytes[10] == "42"): #2DP, Celsius, 2bytes
					#temp = int(bytes[11] + bytes[12],16)
					#dectemp = float(temp)/100
					#self.debugLog(u"Temperature Reported (Node " + str(int(bytes[5],16)) + " Endpoint " + str(endpoint) + "): " + str(dectemp) + " celsius")
					#dev.updateStateOnServer(stateid, dectemp)
					#stampid = stateid + "stamp"
					#timestamp = time.strftime("%d %b %y %H:%M:%S")
					#dev.updateStateOnServer(stampid, str(timestamp))

			if (bytes[7] == "60") and (bytes[8] == "0D") and (bytes[11] == "31") and (bytes[12] == "05"): #MULTI_CHANNEL SENSOR
				#self.debugLog(u"-----")
				#self.debugLog(u"Endpoint Temperature report received:")
				#self.debugLog(u"Raw command: %s" % (byteListStr))
				#self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
				#self.debugLog(u"Endpoint:  %s" % (int(bytes[9],16)))
				#self.debugLog(u"Device:    %s" % (socketMap[int(bytes[9],16)]))
				#self.debugLog(u"Format:    %s" % (bytes[14]))
				#self.debugLog(u"Power (w): %s" % (socketMap[int(bytes[9],16)]))

				bmask = bin(int(bytes[14],16))
				#self.debugLog(str(bmask) + ": " + str(bytes[10]))
				bstr = '00000000' + bmask[2:]
				bstr = bstr[-8:]
				bmdp, bmsc, bmlen = bstr[0:3], bstr[3:5], bstr[5:8]
				#self.debugLog(u"DP: %s, Scale: %s, ByteLength: %s" % ((bmdp,bmsc,bmlen)))
				bmdp = int(bmdp,2)
				bmsc = int(bmsc,2)
				bmlen = int(bmlen,2)
				self.debugLog(u"Bitmask: %s, DP: %s, Scale: %s, ByteLength: %s" % ((bytes[14],bmdp,bmsc,bmlen)))

				if (bmlen == 1):
					value = int(bytes[15],16)
				elif (bmlen == 2):
					value = int(bytes[15] + bytes[16],16)
				elif (bmlen == 4):
					value = int(bytes[15] + bytes[16] + bytes[17] + bytes[18],16)

				value = float(value) / (10**bmdp) # Divide by 10^2 (100) or 10^3 (1000) etc

				if (bmsc == 0): # celsius
					uivalue = value + " °c"
					self.debugLog(u"Temperature Reported (Node " + str(int(bytes[5],16)) + " Endpoint " + str(endpoint) + "): " + str(dectemp) + " celsius")
					stateid = "temp" + str(endpoint)
					if (endpoint == None):
						stateid = "temp1"
				elif (bmsc == 1): # fahrenheit
					uivalue = value + " °f"
					self.debugLog(u"Temperature Reported (Node " + str(int(bytes[5],16)) + " Endpoint " + str(endpoint) + "): " + str(dectemp) + " fahrenheit")
					stateid = "temp" + str(endpoint)
					if (endpoint == None):
						stateid = "temp1"

				dev.updateStateOnServer(stateid, value, uiValue=uivalue)
				stampid = stateid + "stamp"
				timestamp = time.strftime("%d %b %y %H:%M:%S")
				dev.updateStateOnServer(stampid, str(timestamp))


				#stateid = "temp" + str(socketMap[int(bytes[9],16)])
				#self.debugLog(u"State:     %s" % (stateid))
				#if (bytes[14] == "42"): #2DP, Celsius, 2bytes
					#temp = int(bytes[15] + bytes[16],16)
					#dectemp = float(temp)/100
					#self.debugLog(u"Temperature Reported (Node " + str(int(bytes[5],16)) + " *Endpoint " + str(int(bytes[9],16)) + "): " + str(dectemp) + " celsius")
					#dev.updateStateOnServer(stateid, dectemp)
					#stampid = stateid + "stamp"
					#timestamp = time.strftime("%d %b %y %H:%M:%S")
					#dev.updateStateOnServer(stampid, str(timestamp))

##########################################################################################################################################################

	def zwaveCommandSent(self, cmd):
		byteList = cmd['bytes']         # List of the raw bytes just sent.
		byteListStr = convertListToHexStr(byteList)    # this method is defined in the example SDK plugin
		timeDelta = cmd['timeDelta']    # The time duration it took to receive an Z-Wave ACK for the command.
		cmdSuccess = cmd['cmdSuccess']  # True if an ACK was received (or no ACK expected), false if NAK.
		nodeId = cmd['nodeId']          # Can be None!
		endpoint = cmd['endpoint']      # Often will be None!

		bytes = byteListStr.split()

		bytes = byteListStr.split()
		#nodeId = int(bytes[5],16)

		if nodeId:
			if int(nodeId) in self.powerIDs:
				self.debugLog(u"Raw command sent (Node %s): %s (%s)" % (nodeId,byteListStr,cmdSuccess))
			if int(nodeId) in self.tempIDs:
				self.debugLog(u"Raw command sent (Node %s): %s (%s)" % (nodeId,byteListStr,cmdSuccess))


	def getPowerAll(self,pluginAction):
		myDev = pluginAction.deviceId
		node = self.nodeFromDev[int(myDev)]
		self.debugLog("Node: " + str(node))

		codeStr = [0x32, 0x01, 0x10] #32, 01, 10 = Meter_Get, PowerUsed, Wattage

		indigo.server.log("Requesting total power levels for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 1 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=1,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 2 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=2,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 3 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=3,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 4 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=4,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 5 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=5,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 6 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=6,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 7 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=7,cmdBytes=codeStr,sendMode=1)

		indigo.server.log("Requesting power level 8 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=8,cmdBytes=codeStr,sendMode=1)

	def resetPower(self,pluginAction):
		myDev = pluginAction.deviceId
		node = self.nodeFromDev[int(myDev)]
		self.debugLog("Node: " + str(node))
		indigo.server.log("Resetting power levels for node " + str(node))

		indigo.devices[myDev].updateStateOnServer("socket1power",0)
		indigo.devices[myDev].updateStateOnServer("socket2power",0)
		indigo.devices[myDev].updateStateOnServer("socket3power",0)
		indigo.devices[myDev].updateStateOnServer("socket4power",0)
		indigo.devices[myDev].updateStateOnServer("socket5power",0)
		indigo.devices[myDev].updateStateOnServer("socket6power",0)
		indigo.devices[myDev].updateStateOnServer("socket7power",0)
		indigo.devices[myDev].updateStateOnServer("socket8power",0)
		indigo.devices[myDev].updateStateOnServer("totalpowercalc",0)
		indigo.devices[myDev].updateStateOnServer("totalpowerrep",0)
		indigo.devices[myDev].updateStateOnServer("socket1energy",0)
		indigo.devices[myDev].updateStateOnServer("socket2energy",0)
		indigo.devices[myDev].updateStateOnServer("socket3energy",0)
		indigo.devices[myDev].updateStateOnServer("socket4energy",0)
		indigo.devices[myDev].updateStateOnServer("socket5energy",0)
		indigo.devices[myDev].updateStateOnServer("socket6energy",0)
		indigo.devices[myDev].updateStateOnServer("socket7energy",0)
		indigo.devices[myDev].updateStateOnServer("socket8energy",0)
		indigo.devices[myDev].updateStateOnServer("totalenergycalc",0)
		indigo.devices[myDev].updateStateOnServer("totalenergyrep",0)


	def getTempAll(self,pluginAction):
		myDev = pluginAction.deviceId
		node = self.nodeFromDev[int(myDev)]
		self.debugLog("Node: " + str(node))

		codeStr = [0x31, 0x04, 0x05] #32, 01, 10 = Sensor_Get, Humidity

		indigo.server.log("Requesting humidity for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=1,cmdBytes=codeStr,sendMode=2)

		codeStr = [0x31, 0x04, 0x01] #32, 01, 10 = Sensor_Get, Temp

		indigo.server.log("Requesting temperature 1 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=1,cmdBytes=codeStr,sendMode=2)

		indigo.server.log("Requesting temperature 2 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=2,cmdBytes=codeStr,sendMode=2)

		indigo.server.log("Requesting temperature 3 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=3,cmdBytes=codeStr,sendMode=2)

		indigo.server.log("Requesting temperature 4 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=4,cmdBytes=codeStr,sendMode=2)

		indigo.server.log("Requesting temperature 5 for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=5,cmdBytes=codeStr,sendMode=2)

	def getTemp(self,pluginAction):
		myDev = pluginAction.deviceId
		node = self.nodeFromDev[int(myDev)]
		self.debugLog("Node: " + str(node))

		ep = str(pluginAction.props["endpoint"])

		codeStr = [0x31, 0x04, 0x01] #32, 01, 10 = Sensor_Get, Temp

		indigo.server.log("Requesting temperature " + str(ep) + " for node " + str(node))
		indigo.zwave.sendRaw(nodeId=self.nodeFromDev[myDev],endpoint=ep,cmdBytes=codeStr,sendMode=2)
