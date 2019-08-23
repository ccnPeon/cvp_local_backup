import os
import cvp
from cvplibrary import Form, CVPGlobalVariables, GlobalVariableNames

def terminAttrCertEnabled():
   ''' Returns True if TerminAttr cert is enabled.
    Otherwise returns False.
    '''
   server = cvp.Cvp( '127.0.0.1' )
   sid = CVPGlobalVariables.getValue( GlobalVariableNames.CVP_SESSION_ID )
   server.sessionIs( sid )
   return server.getTerminattrCertEnable()

def getIngestAuth( ingestKey ):
   ''' Returns the ingest auth option string.
   '''
   ingestAuth = 'key,' + ingestKey
   if terminAttrCertEnabled():
      ingestAuth = 'token,/tmp/token'
   return ingestAuth

# Using the CVP device interface for receiving telemetry data
ip_list = [ os.environ.get('PRIMARY_DEVICE_INTF_IP', None),
            os.environ.get('SECONDARY_DEVICE_INTF_IP', None),
            os.environ.get('TERTIARY_DEVICE_INTF_IP', None) ]
ingest_grpc = ','.join( [ '%s:9910' % ip for ip in ip_list if ip ] )

# Getting the Ingest Key
# Note: Changing the ingest key requires restarting CVP for the builder to take it.
ingest_key = os.environ.get('AERIS_INGEST_KEY', '')

# Smash tables to exclude
smash_exclude_list = ['ale',
                      'flexCounter',
                      'hardware',
                      'kni',
                      'pulse',
                      'strata']
smash_exclude = ','.join(smash_exclude_list)

# Paths to exclude from the ingest stream
ingest_exclude_list = ['/Sysdb/cell/1/agent',
                       '/Sysdb/cell/2/agent']
ingest_exclude = ','.join(ingest_exclude_list)

# Get Management VRF (allow blank form for default vrf)
ingest_vrf = Form.getFieldById( 'vrf' ).getValue()
if not ingest_vrf:
   ingest_vrf = 'default'

# Print the config
print 'daemon TerminAttr'
print '  exec /usr/bin/TerminAttr -ingestgrpcurl=%s -taillogs ' \
      '-ingestauth=%s -smashexcludes=%s -ingestexclude=%s' \
      % (ingest_grpc, getIngestAuth( ingest_key ), smash_exclude, ingest_exclude) \
      + ((' -ingestvrf=%s' % ingest_vrf) if (ingest_vrf != 'default') else '')
print '  no shutdown'
